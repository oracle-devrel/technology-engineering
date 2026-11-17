export type Lang = "en" | "ar";
const strings = {
  en: {
    appName: "LabSense", tagline: "Order the tests that matter.", patients: "Patients", newConsult: "New consult", resetDemo: "Reset demo data",
    selectPatient: "Choose a patient to begin the consultation", welcomeTitle: "Every test, justified.", welcomeBody: "LabSense checks each requested blood test against the patient's record, flags what is still valid, and keeps a running tally of the cost avoided.",
    you: "Doctor", assistant: "LabSense", placeholder: "Describe the consultation, or paste a photo of an external lab report…", attach: "Attach external lab report", sampleReport: "Load sample external report",
    thinking: "Thinking", send: "Send", stop: "Stop", order: "Order", record: "Record", visits: "Visits", board: "Order board",
    requested: "Requested", recommended: "Recommended", avoidable: "Avoidable", needed: "Order", redundant: "Still valid", expiring: "Expiring soon", lastResult: "Last result", validUntil: "Valid until", noPrior: "No prior result",
    orderPlaced: "Order placed", skipped: "Not repeated", savedThisVisit: "Saved this visit", savedToDate: "Saved to date", spentToDate: "Spent to date", cumulative: "Cumulative savings",
    awaitingOrder: "Ask the doctor's question and the evaluation will appear here.", results: "Results on file", conditions: "Conditions", allergies: "Allergies", medications: "Medications", none: "None recorded",
    visitHistory: "Visit history", noVisits: "First visit. Nothing on file yet.", lastVisit: "Last visit", firstVisit: "First visit", saved: "saved", tests: "tests",
    reviewNote: "AI-assisted. The treating physician decides.", policyNote: "Validity windows are illustrative hospital policy for this demo.",
    gatewayReady: "Dedicated model connected", gatewayOffline: "Gateway offline", connecting: "Connecting…",
    working: "Reviewing the record…", preparingTool: "Preparing the next step…", processingReport: "Reading the report with the model's vision…",
  },
  ar: {
    appName: "لاب سينس", tagline: "اطلب الفحوصات التي تهم فقط.", patients: "المرضى", newConsult: "استشارة جديدة", resetDemo: "إعادة ضبط البيانات",
    selectPatient: "اختر مريضًا لبدء الاستشارة", welcomeTitle: "كل فحص له مبرر.", welcomeBody: "يراجع لاب سينس كل فحص دم مطلوب مقابل سجل المريض، ويحدد ما لا يزال صالحًا، ويحسب التكلفة التي تم تجنبها.",
    you: "الطبيب", assistant: "لاب سينس", placeholder: "صف الاستشارة، أو الصق صورة لتقرير مختبر خارجي…", attach: "إرفاق تقرير مختبر خارجي", sampleReport: "تحميل تقرير خارجي تجريبي",
    thinking: "التفكير", send: "إرسال", stop: "إيقاف", order: "الطلب", record: "السجل", visits: "الزيارات", board: "لوحة الطلب",
    requested: "المطلوب", recommended: "الموصى به", avoidable: "يمكن تجنبه", needed: "اطلب", redundant: "لا يزال صالحًا", expiring: "ينتهي قريبًا", lastResult: "آخر نتيجة", validUntil: "صالح حتى", noPrior: "لا توجد نتيجة سابقة",
    orderPlaced: "تم تسجيل الطلب", skipped: "لم يُكرر", savedThisVisit: "وفّرت هذه الزيارة", savedToDate: "إجمالي التوفير", spentToDate: "إجمالي الإنفاق", cumulative: "التوفير التراكمي",
    awaitingOrder: "اطرح سؤال الطبيب وسيظهر التقييم هنا.", results: "النتائج المسجلة", conditions: "الحالات", allergies: "الحساسية", medications: "الأدوية", none: "لا يوجد",
    visitHistory: "سجل الزيارات", noVisits: "الزيارة الأولى. لا يوجد سجل بعد.", lastVisit: "آخر زيارة", firstVisit: "زيارة أولى", saved: "توفير", tests: "فحوصات",
    reviewNote: "بمساعدة الذكاء الاصطناعي. القرار للطبيب المعالج.", policyNote: "فترات الصلاحية سياسة توضيحية لهذا العرض.",
    gatewayReady: "النموذج المخصص متصل", gatewayOffline: "البوابة غير متصلة", connecting: "جارٍ الاتصال…",
    working: "جارٍ مراجعة السجل…", preparingTool: "جارٍ تجهيز الخطوة التالية…", processingReport: "جارٍ قراءة التقرير…",
  },
} as const;
export type Strings = { [K in keyof (typeof strings)["en"]]: string };
export const t = (lang: Lang): Strings => strings[lang];
