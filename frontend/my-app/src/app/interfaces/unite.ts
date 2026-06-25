export interface Unite {
  id_unite?: number;       // رجعناه اختياري (?) حيت فـ الإضافة (POST) ميكونش عندنا فالبداية
  libelle: string;
  contact?: string;        // اختياري حيت يقدر يكون خاوي فـ قاعدة البيانات
  type: string;

  // 🎯 التعديل الأساسي لدعم حقول المدينة الجديدة
  id_ville?: number;       // المعرف الرقمي للمدينة القادم من Flask
  nom_ville?: string;      // اسم المدينة القادم من Flask لعرضه فـ الجدول
  la_ville?: any;          // خليناه any للمرونة التامة فـ الفورم (يقبل الرقم أو الكائن)
}
