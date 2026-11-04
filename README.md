# Tara by Ability Bazaar

**Transaction and Request Assistant**. Tell us what you need. Tara will guide you through.

Tara is an optional voice/text concierge covering websites, apps, accessibility
testing, document remediation, free apps and the wider Ability Bazaar catalogue.
It explains verified offerings, captures requirements, reads back an editable
draft, prepares existing forms, and guides the visitor into payment checkout.

Integrated prototype: https://www.abilitybazaar.com/tara

PayPal sandbox demonstration: https://www.abilitybazaar.com/tara?demo=1

This repository is an independently runnable source package for the new Tara
layer. The `ability_tara` module, browser client, panel and catalogue match the
integrated release. The small `app.py` harness replaces the private business
platform. Its contact route is an unsent local preview. The integrated site
uses the existing real inquiry form. All Tara-assisted purchases are sandbox-only; normal marketplace checkout remains separate.

## Run locally

Python 3.11 or newer:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set variables from `.env.example` in your shell (it is not automatically loaded).
Local runs default to a bounded **memory store**, so no Firestore account or
Google Cloud sign-in is needed. Use your own paid Gemini API key. For example:

```powershell
$env:GEMINI_API_KEY="your-own-key"
$env:SECRET_KEY="your-own-random-secret"
$env:TARA_STORAGE_BACKEND="memory"
python app.py
```

`/api/health` identifies missing conversation, sandbox or storage configuration;
it does not claim readiness just because the process is running. Memory data is
ephemeral and disappears on restart. For persistent sandbox orders, set
`TARA_STORAGE_BACKEND=firestore`, `GOOGLE_CLOUD_PROJECT`, configure Firestore Native
and ADC/emulator credentials. Cloud Run always uses Firestore; it refuses the
local-memory shortcut. Keep SECRET_KEY stable in hosted deployments.

For PayPal: sign in at https://developer.paypal.com/dashboard/applications/sandbox,
create/select a sandbox REST app and put its client ID and secret in the two
TARA_PAYPAL_SANDBOX variables. Create/use a separate sandbox **buyer** account
for approval. No live payment credential can substitute for a sandbox REST app.

```sh
python app.py
```

Open http://localhost:8080/tara?demo=1. Microphone use needs localhost or HTTPS
and browser permission. All features also have typed controls. The hosted demo
readiness indicator does not imply that a complete buyer capture has been tested.
If sandbox configuration is missing, the app reports that clearly and refuses
to fake a successful checkout.

## Suggested evaluation

1. Ask for a five-page bakery website, compare packages, and choose Starter.
2. Give synthetic requirements and contact details. Review the draft and edit it.
3. Read it aloud if desired, then approve the PayPal sandbox handoff.
4. Sign in with a sandbox buyer and approve. The server verifies the completed
   capture, reference, order ID, USD currency and exact catalogue amount.
5. Try cancellation, refreshing a successful callback, and an unknown question.
6. Try apps, document remediation and custom work; unknown details go to a team
   request preview. The model cannot invent a price or submit the form itself.

Use test details. Sandbox records are separate from real orders and do not
trigger fulfillment, customer messages, lead counts or revenue. PayPal approval
happens on PayPal's own domain; Tara never handles passwords or card details.
Create/capture use idempotency IDs. Pending or mismatched captures are rejected.

## AI, accessibility and limits

Google Gemini provides structured conversation; Aoede provides female voice
with a clear international-English delivery direction. Browser speech recognition
is used where available, with short-recording Gemini transcription as fallback.
Replies stream through Gemini 3.8 Flash TTS as 24 kHz PCM, with Aoede and separate speech-style metadata. Stop, close, hiding the page and a new turn cancel queued speech. The cached welcome and complete-WAV fallback remain available. Tara uses only catalogue and public-page context, with a human-request fallback.
Keyboard controls, visible text, editable details, stop/repeat and draft readback
are included. Assistive-technology and physical-microphone testing are still
required before claiming broad accessibility validation.

Sessions are temporary process memory, not a durable CRM: one worker/instance
is required; a restart loses the active conversation. Use the shared Firestore
daily request ceiling to limit provider calls. It is not an account-wide bill cap.
Google and PayPal accounts/credits are required to run your own copy. The hosted
prototype is provided for evaluation, subject to availability and its daily limit.

## Hackathon scope and disclosure

Ability Bazaar predates the competition. Tara's conversational layer, reviewed
form handoff, price grounding, speech controls and isolated PayPal sandbox path
are new work in November 2026. Do not claim the entire marketplace was built
during this event. AI assistance from ChatGPT/Codex was used for design, coding,
debugging, documentation and validation. This source package does not constitute
a submitted hackathon entry. The hosted sandbox purchase, cancellation and
refresh/idempotency checks passed on November 2; the submission video and final
entry review remain separate tasks. The business platform and earlier submitted
Maya/Saarthi applications remain separate.

Code is MIT licensed. Vision-Aid and Ability Bazaar names and marks identify
their owners; no endorsement by PayPal or Google is implied. Google API output
was used to create the included Aoede welcome recording.

## Explicit two-way voice conversation

Page visits remain silent. Select Talk to Tara or Start voice conversation to
hear the prepared welcome and grant microphone permission. Listening starts
after the welcome and session are ready, then resumes after each complete spoken
reply. Type instead or Stop voice turns it off; close, page hide and navigation
also cancel it, including late permission callbacks. Allowing the microphone is
optional and text mode always works. Permission failures stop automatic retries.

The prepared welcome, brief waiting acknowledgement, streamed replies and WAV
fallback all use Aoede with the same clear international-English direction.
After 1.5 seconds of a slow voice question, Tara can say once, “Thank you. Let me
check that for you.” Fast questions and text mode remain silent. A ready reply
immediately replaces this acknowledgement. It neither repeats forever nor calls
another AI service. Streaming playback still cancels queued audio on Stop/close.

The exact server catalogue, source-grounded assistance, explicit review and
sandbox-only approval boundaries remain unchanged. Speech prompts cannot bypass
payment approval. No API keys, buyer passwords or private business data belong
in this public repository.

## Independent review improvements (3.9.0)

Customer turns are preserved before calling AI. A timeout returns an honest
recovery reply with editable words retained, plus a prepared spoken recovery in
voice mode. The review contains the actual customer wording, not only an AI
summary. Separate package drafts can be resumed without merging their requirements.
Compact catalogue context and minimal thinking reduce unnecessary generation work;
real latency results are reported separately, never promised as a fixed number.

The reviewed, contact-stripped summary is carried into the PayPal sandbox order
description. The verified receipt shows amount/currency, Tara reference, PayPal
order/capture IDs and captured time. The signed cookie retains ownership after
a server restart. A completed PayPal order can be reconciled if capture previously
succeeded but the record update failed. Refresh never intentionally recaptures.

Tara limits use the trusted proxy identity, plus a 60-provider-call session ceiling
and the shared daily ceiling. New cookieless session GETs do not allocate/evict
conversations. Speech has its own concurrency pool. Review pauses microphone input
and announces that approval is still needed. All orders remain sandbox-only.

Run offline checks explicitly:
`python -m pytest -q`
`node --test tests/tara_audio.test.cjs tests/tara_opening.test.cjs`

Catalogue navigation may open the real Ability Bazaar site; the local `/buy/`
path shows a sandbox notice and never redirects into live checkout. This source
has no judge buyer password or API key. Claude independently reviewed the earlier
draft; the team evaluated its findings and implemented accepted changes with Codex.

## Reproduce the synthetic journey evaluation

With the app running, use `python scripts/evaluate_journeys.py --base http://127.0.0.1:8080 --output tara-evaluation`. The explicit target avoids accidentally testing the public site. This makes 60 synthetic journeys / 66 chat turns plus reset requests, uses configured model quota, respects the request throttle and creates no orders, inquiries or emails. It writes full synthetic responses and timing; it is not human usability or assistive-technology testing. For hosted evaluation use a staging URL and ensure quota is available.
