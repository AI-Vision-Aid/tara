"""Customer-word and sandbox failures reproduced by the independent review."""
import copy,hashlib
from unittest import TestCase
from unittest.mock import patch
import app as site
from ability_tara import routes as tara
from ability_tara.memory_store import Store

class ReviewRegressions(TestCase):
    def setUp(self):
        for target,name,value in [(tara,'reserve_call',lambda:True),(tara,'rate_limited',lambda *args:False)]:
            p=patch.object(target,name,value);p.start();self.addCleanup(p.stop)
        self.c=site.app.test_client();self.c.get('/tara?demo=1')
        with self.c.session_transaction() as s:self.h={'X-CSRF-Token':s['csrf_token']}
    def chat(self,text,plan=None,error=None):
        with patch.object(tara,'propose',return_value=plan or {'reply':'Please review.','sku':'static-site','action':'order','fields':{}},side_effect=error):
            return self.c.post('/api/tara/chat',json={'message':text},headers=self.h)
    def test_failed_provider_keeps_verbatim_turn_and_review_then_recovers(self):
        text='Five pages: Home, Menu, Catering, About, Contact. Show opening hours and readable text.'
        data=self.chat(text,error=TimeoutError()).json
        self.assertTrue(data['recovery']);self.assertIn(text,data['customer_words']);self.assertIn(text,data['fields']['notes'])
        self.assertEqual(data['history'][-2]['text'],text);self.assertEqual(data['history'][-1]['id'],'recovery')
        good=self.chat('Choose Starter.').json;self.assertFalse(good['recovery']);self.assertIn(text,good['fields']['notes'])
    def test_stale_ai_summary_cannot_drop_additional_requirements_or_claim_updated(self):
        self.chat('A five-page bakery website.',{'reply':'How can I help?','sku':'static-site','action':'order','fields':{'notes':'A bakery website.'}})
        details='Home, Menu, Catering, About, Contact. Catering form, opening hours, large readable text.'
        data=self.chat(details,{'reply':'I have updated your order details.','sku':'static-site','action':'order','fields':{'notes':'A bakery website.'}}).json
        for term in ['Catering form','opening hours','large readable text']:self.assertIn(term,data['fields']['notes'])
        self.assertNotIn('updated your order',data['history'][-1]['text']);self.assertIn(details,data['customer_words'])
    def test_new_service_preserves_and_can_restore_earlier_draft(self):
        self.chat('A bakery website with catering form.')
        data=self.chat('Now a separate document request: 40 scanned Hindi menus.',{'reply':'Consider Document Standard. How many pages?','sku':'','action':'browse','fields':{}}).json
        self.assertEqual(data['sku'],'doc-standard');self.assertNotIn('catering',data['fields']['notes'])
        self.assertEqual(data['saved_requests'][0]['sku'],'static-site')
        restored=self.c.post('/api/tara/draft',json={'sku':'static-site'},headers=self.h).json
        self.assertIn('catering form',restored['fields']['notes']);self.assertNotIn('Hindi menus',restored['fields']['notes'])
    def test_percentage_is_not_mistaken_for_a_price(self):
        data=self.chat('Can you explain contrast?',{'reply':'Contrast affects 100% of the text, but guarantees need review.','fields':{}}).json
        self.assertIn('100%',data['history'][-1]['text'])
        data=self.chat('I need custom work.',{'reply':'Larger or custom projects need a team-approved quote.','sku':'','action':'browse','fields':{}}).json
        self.assertIn('custom projects',data['history'][-1]['text']);self.assertNotIn('Anything larger projects',data['history'][-1]['text'])
    def test_generated_identifiers_and_website_not_supplied_by_customer_are_removed(self):
        data=self.chat('My email is alex@example.com. I need a bakery website.',{'reply':'Choose Starter Website or App Build [static-site].','sku':'static-site','action':'order','fields':{'target_url':'https://example.com'}}).json
        self.assertNotIn('[static-site]',data['history'][-1]['text']);self.assertNotIn('target_url',data['fields'])
    def test_paypal_summary_carries_requirements_instead_of_contact_details(self):
        summary=tara.payment_summary('Choose Starter Website or App Build. My name is Alex Demo. My email is alex@example.com. Five pages: Home, Menu, Catering, About and Contact. Add a catering form, opening hours and large readable text.')
        for term in ['five pages','catering form','opening hours','readable text']:self.assertIn(term,summary)
        self.assertNotIn('Alex',summary);self.assertNotIn('@',summary)
    def test_cookieless_session_gets_do_not_allocate_or_evict_existing_state(self):
        self.chat('A bakery website.');before=set(tara._states)
        for _ in range(1005):site.app.test_client().get('/api/tara/session')
        self.assertEqual(set(tara._states),before)
    def test_capture_after_restart_has_full_receipt_and_refresh_never_recaptures(self):
        store=Store();fields={'name':'Alex Demo','email':'alex@example.com','notes':'Five bakery pages, catering form and opening hours.'}
        with patch.object(tara,'db',return_value=store),patch.object(tara,'sandbox_ready',return_value=True):
            prep=self.c.post('/api/tara/prepare',json={'kind':'order','sku':'static-site','fields':fields},headers=self.h).json
            with patch.object(tara,'paypal',return_value={'id':'TEST-ORDER','links':[{'rel':'payer-action','href':'https://www.sandbox.paypal.com/checkoutnow?token=TEST-ORDER'}]}) as gateway:
                created=self.c.post('/api/tara/checkout',json={'review_token':prep['review_token'],'confirmed':True},headers=self.h).json
                body=gateway.call_args.args[2];self.assertIn('bakery',body['purchase_units'][0]['description'])
                self.assertNotIn('alex@example.com',str(body));self.assertEqual(body['purchase_units'][0]['amount']['value'],'500.00')
                unit=body['purchase_units'][0];self.assertEqual(unit['amount']['breakdown']['item_total'],unit['items'][0]['unit_amount'])
                self.assertEqual(unit['items'][0]['quantity'],'1');self.assertIn('bakery',unit['items'][0]['description'])
                self.assertEqual(unit['items'][0]['category'],'DIGITAL_GOODS')
            ref=created['reference'];tara._states.clear()
            payload={'id':'TEST-ORDER','status':'COMPLETED','purchase_units':[{'reference_id':ref,'custom_id':ref,'payments':{'captures':[{'id':'TEST-CAPTURE','status':'COMPLETED','create_time':'2026-11-04T01:00:00Z','custom_id':ref,'amount':{'value':'500.00','currency_code':'USD'}}]}}]}
            with patch.object(tara,'paypal',return_value=payload) as gateway:
                url='/tara/paypal/return?ref='+ref+'&token=TEST-ORDER';response=self.c.get(url)
                self.assertEqual(response.status_code,200)
                for term in [b'500.00',b'USD',b'TEST-ORDER',b'TEST-CAPTURE',ref.encode()]:self.assertIn(term,response.data)
                self.assertEqual(self.c.get(url).status_code,200);self.assertEqual(gateway.call_count,1)
                self.assertEqual(site.app.test_client().get(url).status_code,409)
    def test_capture_error_can_reconcile_existing_completed_paypal_order(self):
        store=Store();sid='s'*32;ref='TARA-'+'A'*24
        with self.c.session_transaction() as s:s['tara_sid_sandbox']=sid
        doc=store.collection('tara_demo_orders').document(ref);doc.set({'owner':hashlib.sha256(sid.encode()).hexdigest(),'paypal_order_id':'ORDER','amount':'500.00','status':'created'})
        payload={'id':'ORDER','status':'COMPLETED','purchase_units':[{'reference_id':ref,'payments':{'captures':[{'id':'CAP','status':'COMPLETED','custom_id':ref,'amount':{'value':'500.00','currency_code':'USD'}}]}}]}
        with patch.object(tara,'db',return_value=store),patch.object(tara,'paypal',side_effect=[RuntimeError('AlreadyCaptured'),payload]) as gateway:
            response=self.c.get('/tara/paypal/return?ref='+ref+'&token=ORDER')
        self.assertEqual(response.status_code,200);self.assertEqual(gateway.call_args.args[0],'GET');self.assertEqual(doc.get().to_dict()['status'],'completed')

class TrustedProxyLimits(TestCase):
    def test_rotating_untrusted_forwarded_prefix_does_not_reset_tara_limit(self):
        import security
        security._hits.clear();c=site.app.test_client()
        with c.session_transaction() as session:session['csrf_token']='test-token'
        with c.session_transaction() as s:h={'X-CSRF-Token':s['csrf_token']}
        codes=[]
        with patch.object(tara,'reserve_call',return_value=True):
            for i in range(60):
                response=c.post('/api/tara/chat',json={'message':'Hello'},headers={**h,'X-Forwarded-For':f'192.0.2.{i}, 198.51.100.25'})
                codes.append(response.status_code)
        self.assertEqual(codes.count(429),30);self.assertEqual(codes.count(200),30)
        security._hits.clear()

class PlanConstraints(TestCase):
    def test_schema_cannot_generate_url_queries_or_repeat_customer_notes(self):
        schema=tara.plan_schema({'fields':{},'customer_words':[]},'My name is Alex Demo. My email is alex@example.com. I have 30 Word pages.')
        fields=schema['properties']['fields']['properties']
        self.assertEqual(fields['target_url']['enum'],['']);self.assertEqual(fields['notes']['enum'],[''])
        self.assertIn('Alex Demo',fields['name']['enum']);self.assertIn('alex@example.com',fields['email']['enum'])
        self.assertFalse(schema['additionalProperties']);self.assertEqual(schema['properties']['sources']['maxItems'],6)

class FinalReviewRegressions(TestCase):
    setUp=ReviewRegressions.setUp
    chat=ReviewRegressions.chat
    def test_natural_contact_sentence_stops_before_email_and_preserves_existing_name(self):
        p={'reply':'What pages do you need?','sku':'static-site','action':'order','fields':{}}
        data=self.chat('My name is Test Baker and my email is test.baker@example.com',p).json
        self.assertEqual(data['fields']['name'],'Test Baker');self.assertEqual(data['fields']['email'],'test.baker@example.com')
        again=self.chat('My name is Someone Else.',p).json
        self.assertEqual(again['fields']['name'],'Test Baker')
    def test_organization_is_only_inferred_from_an_explicit_name(self):
        for text in ['My business is a small bakery in Boston and we need five pages','My company is looking for a website']:
            values=tara.literal_fields({'fields':{},'customer_words':[]},text)
            self.assertEqual(values['organization'],[''])
        values=tara.literal_fields({'fields':{},'customer_words':[]},'My company is called Example Bakery and we need five pages.')
        self.assertIn('Example Bakery',values['organization'])
    def test_replacing_a_save_claim_preserves_the_followup_question(self):
        data=self.chat('Please add a gallery.',{'reply':"I've added a gallery to your notes. Do you also need a booking form?",'sku':'static-site','action':'order','fields':{}}).json
        self.assertIn('Do you also need a booking form?',data['history'][-1]['text']);self.assertNotIn("I've added",data['history'][-1]['text'])
    def test_browsing_an_upgrade_does_not_split_the_current_request(self):
        self.chat('Build a bakery website.')
        data=self.chat('What if I later want online ordering?',{'reply':'The Growth Website or App Build may fit later.','sku':'','action':'browse','fields':{}}).json
        self.assertFalse(data['saved_requests']);self.assertIn('bakery',data['fields']['notes'])
    def test_payment_summary_keeps_added_keyboard_requirement_and_named_pages(self):
        text='I need a five-page website for my bakery. Choose Starter Website or App Build. Five pages: Home, Menu, Catering, About and Contact. Add a catering request form, opening hours and large readable text. Please include keyboard-friendly navigation.'
        summary=tara.payment_summary(text)
        self.assertLessEqual(len(summary),127)
        for term in ['five pages','home','menu','catering','about','contact','keyboard-friendly navigation']:self.assertIn(term,summary)
        self.assertIn('more in your Tara brief',tara.bounded_summary('additional detailed requirement '*20))
    def test_edited_paypal_summary_is_sent_without_changing_price(self):
        fields={'name':'Alex Demo','email':'alex@example.com','notes':'Build a bakery website.'}
        with patch.object(tara,'db',return_value=Store()),patch.object(tara,'sandbox_ready',return_value=True):
            prep=self.c.post('/api/tara/prepare',json={'kind':'order','sku':'static-site','fields':fields},headers=self.h).json
            self.assertIn('payment_summary',prep)
            with patch.object(tara,'paypal',return_value={'id':'ORDER','links':[{'rel':'payer-action','href':'https://www.sandbox.paypal.com/checkoutnow?token=ORDER'}]}) as gateway:
                response=self.c.post('/api/tara/checkout',json={'review_token':prep['review_token'],'confirmed':True,'payment_summary':'Five pages; keyboard-friendly navigation','amount':'1.00'},headers=self.h)
                self.assertEqual(response.status_code,200);unit=gateway.call_args.args[2]['purchase_units'][0]
                self.assertEqual(unit['items'][0]['description'],'Five pages; keyboard-friendly navigation');self.assertEqual(unit['amount']['value'],'500.00')
            for summary in ['x'*128,'alex@example.com','https://example.com','']:
                with patch.object(tara,'paypal') as gateway:
                    response=self.c.post('/api/tara/checkout',json={'review_token':prep['review_token'],'confirmed':True,'payment_summary':summary},headers=self.h)
                    self.assertEqual(response.status_code,422);gateway.assert_not_called()
    def test_one_turn_handoff_is_not_duplicated_and_custom_app_routes_to_enterprise(self):
        data=self.chat('Can you promise a native offline iPhone app by tomorrow?',{'reply':'The team must review that.','action':'help','sku':'','fields':{},'interest':'services'}).json
        self.assertNotIn('Customer words:',data['fields']['message'])
        handoff=self.c.post('/api/tara/prepare',json={'kind':'help','fields':{'name':'Alex','email':'alex@example.com','message':data['fields']['message']}},headers=self.h).json
        self.assertEqual(handoff['form']['interest'],'enterprise')

class DocumentScope(ReviewRegressions):
    def test_named_website_pages_without_package_do_not_trigger_document_scope(self):
        data=self.chat('My name is Alex Demo. Organization Demo Bakery. Five pages: Home, Menu, Catering, About and Contact.',{'reply':'Would you like a bakery website?','sku':'','action':'browse','fields':{}}).json
        self.assertNotIn('document remediation',data['history'][-1]['text'])
        self.assertIn('bakery website',data['history'][-1]['text'])
    def test_website_menu_page_is_not_a_document_remediation_request(self):
        data=self.chat('Choose Starter Website or App Build. Five pages: Home, Menu, Catering, About and Contact.',{'reply':'Please review your website request.','sku':'static-site','action':'order','fields':{}}).json
        self.assertNotIn('document remediation',data['history'][-1]['text'])
        self.assertIn('website request',data['history'][-1]['text'])
    def test_unconfirmed_scanned_document_scope_is_not_calculated_as_a_known_page_total(self):
        data=self.chat('I have 40 scanned Hindi menus; page count unknown.',{'reply':'Your 40 menus fit Standard at 80 pages.','sku':'doc-standard','action':'browse','fields':{}}).json
        self.assertNotIn('80 pages',data['history'][-1]['text']);self.assertIn('confirm',data['history'][-1]['text'])
