import os
from unittest import TestCase
from unittest.mock import patch
import app
from ability_tara import routes as tara

class LocalSetup(TestCase):
    def test_no_firestore_local_setup_is_honest_and_can_run_a_turn(self):
        with patch.dict(os.environ,{},clear=True):
            c=app.app.test_client();health=c.get('/api/health').json
            self.assertFalse(health['ready']);self.assertTrue(health['storage_configured'])
            self.assertEqual(health['status'],'needs_configuration')
            c.get('/tara?demo=1')
            with c.session_transaction() as s:h={'X-CSRF-Token':s['csrf_token']}
            with patch.object(tara,'propose',return_value={'reply':'What do you need?','fields':{}}):
                response=c.post('/api/tara/chat',json={'message':'A custom website with a booking form.'},headers=h)
            self.assertEqual(response.status_code,200)
    def test_local_buy_link_never_redirects_to_real_checkout(self):
        response=app.app.test_client().get('/buy/static-site')
        self.assertEqual(response.status_code,200);self.assertNotIn('Location',response.headers)
    def test_local_memory_is_never_selected_inside_cloud_run(self):
        with patch.dict(os.environ,{'K_SERVICE':'cloud-service','TARA_STORAGE_BACKEND':'memory'}),app.app.test_request_context('/'):
            self.assertFalse(tara.local_storage())
