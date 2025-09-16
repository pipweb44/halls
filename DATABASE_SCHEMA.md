# مخطط قاعدة البيانات لنظام حجز القاعات

## جدول المحافظات (Governorate)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| name | CharField | اسم المحافظة |
| name_en | CharField | الاسم بالإنجليزية |
| code | CharField | كود المحافظة |
| region | CharField | المنطقة (القاهرة الكبرى، الدلتا، إلخ) |
| created_at | DateTimeField | تاريخ الإنشاء |

## جدول المدن (City)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| name | CharField | اسم المدينة/المركز |
| name_en | CharField | الاسم بالإنجليزية |
| governorate | ForeignKey | المحافظة التابعة لها |
| is_capital | BooleanField | هل هي عاصمة المحافظة؟ |
| created_at | DateTimeField | تاريخ الإنشاء |

## جدول الفئات (Category)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| name | CharField | اسم الفئة |
| description | TextField | الوصف |
| icon | CharField | الأيقونة |

## جدول القاعات (Hall)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| name | CharField | اسم القاعة |
| category | ForeignKey | الفئة |
| governorate | ForeignKey | المحافظة |
| city | ForeignKey | المدينة/المركز |
| address | TextField | العنوان التفصيلي |
| description | TextField | الوصف |
| capacity | PositiveIntegerField | السعة |
| price_per_hour | DecimalField | السعر للساعة |
| image | ImageField | الصورة الرئيسية |
| status | CharField | الحالة (متاح، صيانة، محجوز) |
| features | JSONField | المميزات |
| phone | CharField | رقم الهاتف |
| email | EmailField | البريد الإلكتروني |
| website | URLField | الموقع الإلكتروني |
| latitude | DecimalField | خط العرض |
| longitude | DecimalField | خط الطول |
| created_at | DateTimeField | تاريخ الإنشاء |
| updated_at | DateTimeField | تاريخ التحديث |

## جدول صور القاعات (HallImage)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| hall | ForeignKey | القاعة |
| image | ImageField | الصورة |
| image_type | CharField | نوع الصورة (رئيسية، معرض، إلخ) |
| title | CharField | عنوان الصورة |
| description | TextField | وصف الصورة |
| is_featured | BooleanField | صورة مميزة |
| order | PositiveIntegerField | ترتيب العرض |
| uploaded_at | DateTimeField | تاريخ الرفع |

## جدول الحجوزات (Booking)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| booking_id | UUIDField | معرف الحجز الفريد |
| hall | ForeignKey | القاعة |
| user | ForeignKey | المستخدم |
| customer_name | CharField | اسم العميل |
| customer_email | EmailField | البريد الإلكتروني للعميل |
| customer_phone | CharField | هاتف العميل |
| event_title | CharField | عنوان الحدث |
| event_description | TextField | وصف الحدث |
| start_datetime | DateTimeField | تاريخ ووقت البداية |
| end_datetime | DateTimeField | تاريخ ووقت النهاية |
| attendees_count | PositiveIntegerField | عدد الحضور |
| total_price | DecimalField | السعر الإجمالي |
| status | CharField | حالة الحجز (في الانتظار، موافق عليه، إلخ) |
| admin_notes | TextField | ملاحظات الإدارة |
| created_at | DateTimeField | تاريخ الطلب |
| updated_at | DateTimeField | تاريخ التحديث |

## جدول مديري القاعات (HallManager)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| user | OneToOneField | المستخدم |
| hall | OneToOneField | القاعة |
| permission_level | CharField | مستوى الصلاحية |
| assigned_at | DateTimeField | تاريخ التعيين |
| is_active | BooleanField | نشط |
| notes | TextField | ملاحظات |

## جدول الاتصالات (Contact)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| name | CharField | الاسم |
| email | EmailField | البريد الإلكتروني |
| phone | CharField | رقم الهاتف |
| subject | CharField | الموضوع |
| message | TextField | الرسالة |
| created_at | DateTimeField | تاريخ الإرسال |
| is_read | BooleanField | مقروءة |

## جدول الإشعارات (Notification)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| user | ForeignKey | المستخدم |
| booking | ForeignKey | الحجز (اختياري) |
| notification_type | CharField | نوع الإشعار |
| title | CharField | العنوان |
| message | TextField | الرسالة |
| is_read | BooleanField | مقروء |
| created_at | DateTimeField | تاريخ الإنشاء |

## العلاقات بين الجداول
1. **المدينة (City) → المحافظة (Governorate)**: علاقة many-to-one (مدينة واحدة تنتمي لمحافظة واحدة)
2. **القاعة (Hall) → الفئة (Category)**: علاقة many-to-one (قاعة واحدة تنتمي لفئة واحدة)
3. **القاعة (Hall) → المحافظة (Governorate)**: علاقة many-to-one (قاعة واحدة في محافظة واحدة)
4. **القاعة (Hall) → المدينة (City)**: علاقة many-to-one (قاعة واحدة في مدينة واحدة)
5. **صورة القاعة (HallImage) → القاعة (Hall)**: علاقة many-to-one (عدة صور لقاعة واحدة)
6. **الحجز (Booking) → القاعة (Hall)**: علاقة many-to-one (عدة حجوزات لقاعة واحدة)
7. **الحجز (Booking) → المستخدم (User)**: علاقة many-to-one (عدة حجوزات لمستخدم واحد)
8. **مدير القاعة (HallManager) → المستخدم (User)**: علاقة one-to-one (مدير واحد لكل مستخدم)
9. **مدير القاعة (HallManager) → القاعة (Hall)**: علاقة one-to-one (مدير واحد لكل قاعة)
10. **الإشعار (Notification) → المستخدم (User)**: علاقة many-to-one (عدة إشعارات لمستخدم واحد)
11. **الإشعار (Notification) → الحجز (Booking)**: علاقة many-to-one (عدة إشعارات لحجز واحد)

## مؤشرات الأداء
يتم استخدام الفهارس التالية لتحسين أداء الاستعلامات:
- فهارس تلقائية على الحقول الأساسية (id)
- فهارس على الحقول المستخدمة في عمليات البحث والتصفية
- فهارس فريدة على الأزواج الفريدة من الحقول

## قيود النزاهة
- القيم الفارغة غير مسموح بها في الحقول الإلزامية
- القيم الفريدة مفروضة على الحقول المطلوبة
- قيود التكامل المرجعي مفعلة على جميع العلاقات
