# WhatsApp Bot — Setup Guide (simple bhasha me)

Ye bot tumhare WhatsApp Business number par aane wale messages ka **human-jaisa jawab** dega — tum online raho ya off.

Technical kaam (server, tunnel, bot code) main sambhal lunga. **Neeche wale 5 steps tumhe khud karne honge**, kyunki inme tumhare Meta/Facebook account ka login lagta hai.

---

## Step 1 — Meta developer account aur app banao

1. **developers.facebook.com** kholo aur apne Facebook account se login karo.
2. **"Create App"** dabao → app type **"Business"** chuno → app ka naam kuch bhi rakho (jaise "Mera WhatsApp Bot").
3. App ke dashboard me **"Add Product"** me jao aur **WhatsApp** product add karo.

## Step 2 — Apna EXISTING WhatsApp Business number migrate karo

> ⚠️ **Sabse pehle BACKUP le lo!** Apne WhatsApp Business app me **Settings → Chats → Chat backup** me jao aur backup complete kar lo. **Migration ke baad tumhara number WhatsApp Business app se disconnect ho jayega** — app me us number se message bhejna/receive karna band ho jayega. Purani chats app me tabhi dikhengi agar backup liya hoga.

1. Meta App Dashboard me **WhatsApp → API Setup** kholo.
2. Wahan **"migrate existing number"** (ya "Add phone number" → existing number wala option) chuno.
3. Apna wahi WhatsApp Business number dalo jo abhi app me chal raha hai, aur OTP se verify karo.

> 📌 **Yaad rakho:** Migration ke baad us number ke **saare messages sirf API/bot ke through** jayenge. Matlab customers ko jawab ab bot dega, WhatsApp app se nahi. Isi liye naya number lene ke bajaye tumne apna purana number migrate karne ka faisla kiya hai — taaki customers ko naya number na dena pade.

## Step 3 — Permanent access token banao

1. App Dashboard me **WhatsApp → API Setup** me hi tumhe ek temporary token dikhega — wo kuch ghanto me expire ho jata hai, use mat lo.
2. **Business Settings → Users → System Users** me jao, ek system user banao, usko WhatsApp app ka admin access do, aur **permanent token** generate karo (permissions: `whatsapp_business_messaging`, `whatsapp_business_management`).
3. Is token ko **kisi ko mat bhejo, kahin post mat karo** — bas mujhe (assistant ko) chat me de dena, main ise seedha `config.json` me daal dunga.

## Step 4 — Webhook set karo

1. App Dashboard me **WhatsApp → Configuration → Webhook** kholo.
2. **Callback URL** me Render wala URL dalo (deploy ke baad milega — mujhse maang lena), uske aage `/webhook` lagakar.
   - Jaise: `https://whatsapp-bot-webhook-xxxx.onrender.com/webhook`
3. **Verify token** me Render dashboard me dikh rahi **VERIFY_TOKEN** ki value dalo.
   (Render dashboard → tumhari web service → **Environment** tab me milegi.)
4. **Verify and Save** dabao → uske baad **"messages"** field par **Subscribe** karo.

> Agar "Verify and Save" fail ho to mujhe batao — matlab mera server us waqt online nahi tha, main use chalu kar dunga.

## Step 5 — Mujhe ye 3 cheezein bhej do

Chat me bas itna likh bhejo, main `config.json` me daal dunga:

- **phone_number_id** (API Setup page par "Phone number ID" likha milega)
- **waba_id** (WhatsApp Business Account ID)
- **access token** (Step 3 wala permanent token)

Bas! Uske baad main bot ko live kar dunga aur test message bhejkar confirm karunga.

---

## Bot rokna / chalu karna (PAUSED wala rule)

- Agar tum chaho ki bot **jawab dena band** kar de, to bas mujhse kaho: **"bot rok do"**.
- Wapas chalu karne ke liye kaho: **"bot chalu karo"**.

Technical me ye aise kaam karta hai: project folder me `PAUSED` naam ki ek khaali file bana di jati hai. Jab tak ye file hai, reply loop koi message **bhejega nahi** (aane wale messages `inbox/` me save hote rahenge). File hatate hi bot phir se jawab dene lagta hai. Tumhe file khud banane/hatane ki zaroorat nahi — bas mujhe bol do.

---

## 🚀 Deploy — Render (free hosting) par receiver chalana

**Naya architecture (final):** Meta ke messages receive karne ke liye ek public
server chahiye. Wo **Render** (free) par chalega — `webhook.py` wahan deploy
hoga. Message ka **jawab** main (assistant) dunga: mera reply loop har minute
Render se naye messages lega (`/pending`), human-jaisa jawab banayega, aur
WhatsApp Cloud API se seedha bhej dega. Isliye Render ko WhatsApp ka token
**nahi** chahiye — token sirf mere paas `config.json` me rahega.

### Render par deploy kaise hoga (assistant karega, tum bas accounts banao)

1. **GitHub account** banao (free) — github.com par signup.
2. **Render account** banao (free) — render.com par "Sign up with GitHub".
3. Uske baad mujhe bolo — main tumhare saath browser me step-by-step deploy
   kar dunga: GitHub me repo banana + code upload, Render me web service
   banana (`render.yaml` blueprint taiyaar hai), aur uska public URL nikalna.

Deploy ke baad Render tumhe ek URL dega, jaise
`https://whatsapp-bot-webhook-xxxx.onrender.com` — **wahi URL Step 4
(Webhook) me Callback URL ki jagah dalna hai**, `/webhook` lagakar:
`https://whatsapp-bot-webhook-xxxx.onrender.com/webhook`

> ⚠️ Free plan ki ek limit: 15 minute koi activity na ho to Render ka server
> "so jata" hai, aur pehla message thoda late (30–60 second) pahunch sakta
> hai. Business ke liye baad me paid plan ($7/month) lena behtar rahega —
> lekin shuruaat free se ho jayegi.

### Purana tunnel wala note (ab lagu nahi)

Pehle plan tha ki tunnel (cloudflared) se public URL banaya jaye, lekin is
machine ka network tunnel banane nahi deta. Isliye ab Render wala rasta final
hai — `public_url.txt` aur `start.sh` wala local-tunnel setup ab backup ke
taur par hi rakha hai.
