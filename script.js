function copyEmail() {
    const emailInput = document.getElementById('emailInput');
    if (!emailInput) return;
    emailInput.select();
    navigator.clipboard.writeText(emailInput.value);
    
    const copyBtn = document.querySelector('.copy-btn');
    if (copyBtn) {
        copyBtn.innerText = "Copied!";
        setTimeout(() => {
            copyBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy`;
        }, 2000);
    }
}

// Global Languages Dictionary
const translations = {
    en: {
        heroTitle: "Instant Temporary Email",
        heroSub: "Get a disposable email address in seconds. Keep your real inbox safe, private and spam-free.",
        copyBtn: "Copy",
        newBtn: "New Email",
        activeTimer: "Active for:"
    },
    es: { // Spanish
        heroTitle: "Correo Temporal Instantáneo",
        heroSub: "Obtenga una dirección de correo electrónico desechable en segundos. Mantenga su bandeja de entrada real segura, privada y sin spam.",
        copyBtn: "Copiar",
        newBtn: "Nuevo Correo",
        activeTimer: "Activo por:"
    },
    fr: { // French
        heroTitle: "E-mail Temporaire Instantané",
        heroSub: "Obtenez une adresse e-mail jetable en quelques secondes. Gardez votre vraie boîte de réception sûre et sans spam.",
        copyBtn: "Copier",
        newBtn: "Nouvel E-mail",
        activeTimer: "Actif pendant :"
    },
    de: { // German
        heroTitle: "Sofortige Wegwerf-E-Mail",
        heroSub: "Erhalten Sie in Sekundenschnelle eine temporäre E-Mail-Adresse. Schützen Sie Ihren Posteingang vor Spam.",
        copyBtn: "Kopieren",
        newBtn: "Neue E-Mail",
        activeTimer: "Aktiv für:"
    },
    ar: { // Arabic
        heroTitle: "بريد مؤقت فوري",
        heroSub: "احصل على عنوان بريد إلكتروني مؤقت في ثوانٍ. حافظ على بريدك الحقيقي آمنًا وخاليًا من الرسائل غير المرغوب فيها.",
        copyBtn: "نسخ",
        newBtn: "بريد جديد",
        activeTimer: "نشط لمدة:"
    },
    zh: { // Chinese
        heroTitle: "即时临时电子邮件",
        heroSub: "几秒钟内获取一次性电子邮件地址。保持您的真实收件箱安全、私密且无垃圾邮件。",
        copyBtn: "复制",
        newBtn: "新邮件",
        activeTimer: "有效时间："
    }
};

// Language Switcher Function
function changeLanguage(lang) {
    const t = translations[lang];
    if (!t) return;

    const titleEl = document.querySelector('.hero-card h1');
    const subEl = document.querySelector('.hero-sub');
    const newBtnEl = document.querySelector('.new-btn');
    
    if (titleEl) titleEl.innerText = t.heroTitle;
    if (subEl) subEl.innerText = t.heroSub;
    if (newBtnEl) newBtnEl.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#04060a" stroke-width="2.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg> ${t.newBtn}`;
}