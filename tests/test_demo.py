"""Offline checks; no keys, cloud writes, payments or messages are needed."""
import copy
import unittest
from unittest.mock import patch
import app
from ability_tara import routes as tara


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.client=app.app.test_client()
        self.client.get('/tara?demo=1')
        with self.client.session_transaction() as s:self.headers={'X-CSRF-Token':s['csrf_token']}

    def test_accessible_page_and_required_consent_controls(self):
        page=self.client.get('/tara?demo=1')
        self.assertEqual(page.status_code,200)
        self.assertIn(b'Start voice conversation',page.data)
        self.assertIn(b'Read my draft aloud',page.data)
        self.assertIn(b'PayPal sandbox demo',page.data)

    def test_welcome_is_prepared_and_catalogue_introductions_need_no_provider(self):
        self.assertEqual(self.client.get('/static/audio/tara/welcome-v381.mp3').status_code,200)
        with patch.object(tara,'propose') as provider,patch.object(tara,'reserve_call',return_value=False):
            response=self.client.post('/api/tara/chat',json={'message':'Tell me about your free apps.'},headers=self.headers)
        self.assertEqual(response.status_code,200)
        self.assertIn('Maya',response.json['history'][-1]['text'])
        provider.assert_not_called()

    def test_csrf_precedes_any_provider_call(self):
        with patch.object(tara,'propose') as model:
            self.assertEqual(self.client.post('/api/tara/chat',json={'message':'Hello'}).status_code,400)
            model.assert_not_called()

    def test_real_catalogue_overrules_generated_price(self):
        with patch.object(tara,'reserve_call',return_value=True),patch.object(tara,'propose',return_value={
            'reply':'Pay only $1.','sku':'static-site','action':'order','fields':{}}):
            response=self.client.post('/api/tara/chat',json={'message':'Website please','mode':'sandbox'},headers=self.headers)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json['item']['price_usd'],500)
            self.assertNotIn('$1.',response.json['history'][-1]['text'])

    def test_review_cannot_be_skipped(self):
        with patch.object(tara,'paypal') as provider:
            response=self.client.post('/api/tara/checkout',json={'confirmed':True,'review_token':'fake'},headers=self.headers)
            self.assertEqual(response.status_code,409)
            provider.assert_not_called()

    def test_missing_sandbox_config_is_not_success(self):
        with patch.object(tara,'sandbox_ready',return_value=False):
            self.assertFalse(self.client.get('/api/tara/session?mode=sandbox').json['sandbox_ready'])

    def test_capture_must_match_actual_completed_amount(self):
        ref='TARA-'+'A'*24;order={'paypal_order_id':'TEST','amount':'500.00'}
        payload={'id':'TEST','status':'COMPLETED','purchase_units':[{'reference_id':ref,'custom_id':ref,
            'payments':{'captures':[{'status':'COMPLETED','custom_id':ref,'amount':{'currency_code':'USD','value':'500.00'}}]}}]}
        self.assertTrue(tara.verified_capture(payload,order,ref))
        for value in ['0.01','499.99','501.00']:
            bad=copy.deepcopy(payload);bad['purchase_units'][0]['payments']['captures'][0]['amount']['value']=value
            self.assertFalse(tara.verified_capture(bad,order,ref))
        bad=copy.deepcopy(payload);bad['purchase_units'][0]['payments']['captures'][0]['status']='PENDING'
        self.assertFalse(tara.verified_capture(bad,order,ref))

if __name__=='__main__':unittest.main()
