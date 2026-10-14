import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import evaluate
import run
from validate import validate_si_complete
from discover.publishers.elsevier import ElsevierAdapter
from discover.publishers.wiley import WileyAdapter


class Response:
    def __init__(self, url, status=200, text='', headers=None):
        self.url = url
        self.status_code = status
        self.text = text
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f'HTTP {self.status_code}')


class RegressionTests(unittest.TestCase):
    def test_no_discovered_si_is_unknown(self):
        self.assertIsNone(validate_si_complete([], []))

    def test_failed_si_is_not_complete(self):
        self.assertFalse(validate_si_complete(['https://example.org/si'], []))

    def test_valid_discovered_si_still_passes(self):
        self.assertTrue(validate_si_complete(['https://example.org/si'], [{'valid': True}]))

    def test_normalized_duplicates_are_acquired_once_and_invalid_does_not_stop_batch(self):
        with patch('run.acquire', return_value={'status': 'partial'}) as acquire:
            with contextlib.redirect_stdout(io.StringIO()):
                run.run_many(['10.1234/ABC', 'https://doi.org/10.1234/abc',
                              'invalid', 'doi:10.1234/def'])
        self.assertEqual([c.args[0] for c in acquire.call_args_list],
                         ['10.1234/abc', '10.1234/def'])

    def test_missing_manifest_remains_in_fixed_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / 'sample.txt'
            sample.write_text('10.1234/a\nhttps://doi.org/10.1234/A\n10.1234/b\ninvalid\n')
            output = root / 'output'
            for name, doi in [('a', '10.1234/a'), ('outside', '10.1234/outside')]:
                folder = output / name
                folder.mkdir(parents=True)
                (folder / 'manifest.json').write_text(json.dumps({
                    'doi': doi, 'publisher': 'Test', 'status': 'partial',
                    'fulltext': {'valid': True, 'format': 'pdf', 'source': 'Test'}}))
            with patch.object(evaluate, 'OUTPUT_DIR', output):
                with contextlib.redirect_stdout(io.StringIO()) as stdout:
                    # Default evaluation must use the fixed sample, not output count.
                    with patch.object(evaluate, 'DOI_FILE', sample, create=True):
                        manifests = evaluate.load_manifests()
                    evaluate.evaluate(manifests)
            self.assertEqual({m['doi'] for m in manifests}, {'10.1234/a', '10.1234/b'})
            self.assertIn('Full-text acquisition: 1/2 (50.0%)', stdout.getvalue())
            missing = next(m for m in manifests if m['doi'] == '10.1234/b')
            self.assertEqual(missing['status'], 'failed')

    def test_elsevier_api_survives_landing_page_failure(self):
        with patch.dict('os.environ', {'ELSEVIER_API_KEY': 'test-only-placeholder'}):
            with patch('discover.publishers.elsevier.requests.get',
                       return_value=Response('https://example.org', 403)):
                try:
                    result = ElsevierAdapter().discover('10.1016/test')
                except Exception as exc:
                    self.fail(f'Landing page blocked independent API: {exc}')
        self.assertEqual([c['format'] for c in result['fulltext_candidates']], ['pdf', 'xml'])

    def test_wiley_api_survives_landing_page_failure(self):
        def get(url, **kwargs):
            if url.startswith('https://api.wiley.com/'):
                return Response(url, 302, headers={'Location': 'https://example.org/article.pdf'})
            return Response(url, 403)
        with patch.dict('os.environ', {'WILEY_API_KEY': 'test-only-placeholder'}):
            with patch('discover.publishers.wiley.requests.get', side_effect=get):
                try:
                    result = WileyAdapter().discover('10.1002/test')
                except Exception as exc:
                    self.fail(f'Landing page blocked independent API: {exc}')
        self.assertEqual(result['fulltext_candidates'][0]['url'], 'https://example.org/article.pdf')

    def test_empty_output_keeps_all_valid_sample_dois(self):
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / 'sample.txt'
            sample.write_text('10.1234/a\n10.1234/b\n')
            with patch.object(evaluate, 'OUTPUT_DIR', Path(tmp) / 'absent'):
                results = evaluate.load_manifests(sample)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(m['status'] == 'failed' for m in results))

    def test_corrupt_manifest_still_counts_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / 'sample.txt'
            sample.write_text('10.1234/a\n')
            folder = root / 'output' / 'a'
            folder.mkdir(parents=True)
            (folder / 'manifest.json').write_text('{broken')
            with patch.object(evaluate, 'OUTPUT_DIR', root / 'output'):
                with contextlib.redirect_stdout(io.StringIO()):
                    results = evaluate.load_manifests(sample)
        self.assertEqual(results[0]['doi'], '10.1234/a')
        self.assertEqual(results[0]['status'], 'failed')

    def test_page_failure_without_api_still_raises(self):
        for module, adapter in [('elsevier', ElsevierAdapter), ('wiley', WileyAdapter)]:
            with self.subTest(publisher=module), patch.dict('os.environ', {}, clear=True):
                with patch(f'discover.publishers.{module}.requests.get',
                           return_value=Response('https://example.org', 403)):
                    with self.assertRaisesRegex(RuntimeError, '403'):
                        adapter().discover('10.1234/test')

    def test_healthy_pages_preserve_pdf_and_si_discovery(self):
        html = ('<meta name="citation_pdf_url" content="https://example.org/article.pdf">'
                '<a href="/mmc1.pdf">supplement</a>'
                '<a href="/downloadSupplement/si.zip">SI</a>')
        for module, adapter, si in [
            ('elsevier', ElsevierAdapter, 'https://example.org/mmc1.pdf'),
            ('wiley', WileyAdapter, 'https://example.org/downloadSupplement/si.zip'),
        ]:
            with self.subTest(publisher=module), patch.dict('os.environ', {}, clear=True):
                with patch(f'discover.publishers.{module}.requests.get',
                           return_value=Response('https://example.org/article', text=html)):
                    result = adapter().discover('10.1234/test')
            self.assertEqual(result['fulltext_candidates'][0]['url'],
                             'https://example.org/article.pdf')
            self.assertIn(si, result['si_urls'])


if __name__ == '__main__':
    unittest.main()
