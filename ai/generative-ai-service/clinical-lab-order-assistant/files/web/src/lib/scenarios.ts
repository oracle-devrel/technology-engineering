/** Demo starters per fictional patient. Index 0 is the main storyline. */
export const scenarios: Record<string, { en: string[]; ar: string[] }> = {
  "PT-100234": {
    en: [
      "Fatimah is back with dizziness on standing and tiredness. I want to order CBC, metabolic panel, lipid panel, HbA1c, TSH, vitamin D and urinalysis.",
      "She mentions palpitations since last week. Does that change what we repeat?",
      "Confirm the order as recommended and summarise the visit.",
    ],
    ar: [
      "فاطمة تعاني من دوخة عند الوقوف وتعب. أريد طلب تعداد الدم، لوحة الأيض، الدهنيات، السكر التراكمي، الغدة الدرقية، فيتامين د وتحليل البول.",
      "تشكو من خفقان منذ الأسبوع الماضي. هل يغير ذلك ما نكرره؟",
      "أكّد الطلب كما هو موصى به ولخّص الزيارة.",
    ],
  },
  "PT-100871": {
    en: [
      "Mohammed wants a full check-up before starting a gym programme. Order CBC, metabolic panel, lipid panel, HbA1c, TSH and vitamin D.",
      "He brought a lab report from another clinic. Read it, add the results to his record and re-evaluate the order.",
      "Confirm the reduced order and summarise the visit.",
    ],
    ar: [
      "محمد يريد فحصًا شاملاً قبل بدء برنامج رياضي. اطلب تعداد الدم، لوحة الأيض، الدهنيات، السكر التراكمي، الغدة الدرقية وفيتامين د.",
      "أحضر تقريرًا من عيادة أخرى. اقرأه وأضف النتائج إلى سجله ثم أعد التقييم.",
      "أكّد الطلب المختصر ولخّص الزيارة.",
    ],
  },
  "PT-101455": {
    en: [
      "Noura is here for her anaemia follow-up. Order CBC, ferritin and iron studies, B12, vitamin D and TSH.",
      "Her last ferritin was still low. Is it worth repeating the CBC six weeks on?",
      "Confirm the order and summarise the visit.",
    ],
    ar: [
      "نورة هنا لمتابعة فقر الدم. اطلب تعداد الدم، الفيريتين ومخزون الحديد، ب12، فيتامين د والغدة الدرقية.",
      "آخر فيريتين كان منخفضًا. هل يستحق تكرار تعداد الدم بعد ستة أسابيع؟",
      "أكّد الطلب ولخّص الزيارة.",
    ],
  },
  "PT-102003": {
    en: [
      "Khalid is a new patient with hypertension. Baseline work-up: CBC, metabolic panel, lipid panel, HbA1c, urinalysis, urine albumin ratio and blood group.",
      "Why is nothing flagged as redundant for him?",
      "Confirm the full baseline order and summarise the visit.",
    ],
    ar: [
      "خالد مريض جديد بارتفاع ضغط الدم. فحوصات أساسية: تعداد الدم، لوحة الأيض، الدهنيات، السكر التراكمي، تحليل البول، نسبة الألبومين وفصيلة الدم.",
      "لماذا لم يُعلَّم أي فحص على أنه مكرر له؟",
      "أكّد الطلب الأساسي الكامل ولخّص الزيارة.",
    ],
  },
};
export const sampleReportPatient = "PT-100871";
export const sampleReportPath = "/samples/al-noor-lab-report.png";
