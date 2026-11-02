"""Independently runnable Tara sandbox. The business marketplace stays separate."""
import json,os,secrets
from pathlib import Path
from flask import Flask,redirect,render_template_string,request
from werkzeug.middleware.proxy_fix import ProxyFix
from security import get_csrf_token
from ability_market.catalogue import CATALOGUE,get_buyable
from ability_tara.routes import bp

app=Flask(__name__)
app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1,x_host=1)
app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
                  SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',
                  SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE','0')=='1')
APPS=json.loads((Path(__file__).parent/'public_apps.json').read_text(encoding='utf-8'))
TARA_REFERENCE_PAGES=json.loads((Path(__file__).parent/'public_pages.json').read_text(encoding='utf-8'))
INTERESTS=[('services','Services'),('app-pilot','App pilot'),('enterprise','Custom app'),
           ('sponsor','Sponsorship'),('creator','Creator'),('tester','Tester'),('partner','Partnership'),('other','Other')]
app.register_blueprint(bp)

@app.context_processor
def context():
    return {'csrf_token':get_csrf_token(),'tara_catalogue':CATALOGUE,'current_path':request.path}

@app.before_request
def default_demo():
    if request.path=='/' or (request.path=='/tara' and request.args.get('demo')!='1'):
        return redirect('/tara?demo=1')

@app.after_request
def headers(response):
    response.headers.update({'X-Content-Type-Options':'nosniff','X-Frame-Options':'SAMEORIGIN',
        'Referrer-Policy':'strict-origin-when-cross-origin','Cache-Control':'no-store',
        'Permissions-Policy':'microphone=(self), camera=(), geolocation=()',
        'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' blob: data:; object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self' https://www.sandbox.paypal.com"})
    return response

@app.get('/api/health')
def health():return {'status':'ok','app':'tara-sandbox'}

@app.get('/privacy')
def privacy():
    return render_template_string("""{% extends 'base.html' %}{% block content %}<section class='section'><div class='container'><h1>Tara demo privacy</h1><p>Use synthetic details. Gemini processes conversation and voice; your browser may use its speech provider. Start voice requires your action and microphone permission. Conversation is temporary, stored in process memory for up to two hours of inactivity. Sandbox transaction status and the test brief are stored in your configured Firestore project. No live payments, fulfillment or emails are sent. Tab-local form handoff expires after fifteen minutes.</p><a href='/tara?demo=1'>Return to Tara</a></div></section>{% endblock %}""",page_title='Privacy')

@app.get('/services')
@app.get('/apps')
@app.get('/sponsor')
@app.get('/donate')
@app.get('/about')
@app.get('/support')
@app.get('/terms')
@app.get('/apps/<path:rest>')
@app.get('/buy/<path:sku>')
def published_info(**kwargs):return redirect('https://www.abilitybazaar.com'+request.path)

@app.get('/contact')
def contact_preview():
    return render_template_string("""{% extends 'base.html' %}{% block content %}<section class='section'><div class='container'><h1>Local request preview</h1><p>This standalone demo does not send team requests. The integrated Ability Bazaar site has the real contact form. Review this preview, or visit Ability Bazaar to submit a real inquiry.</p><form action='/contact'><label>Name<input name='name'></label><label>Email<input name='email'></label><label>Organization<input name='organization'></label><select name='interest'><option value='other'>Other</option><option value='services'>Services</option></select><label>Question<textarea name='message'></textarea></label></form><a href='https://www.abilitybazaar.com/contact'>Open the real contact form</a></div></section>{% endblock %}""",page_title='Request preview')

if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT','8080')),threaded=True)
