# مخطط قاعدة البيانات لنظام حجز القاعات (بعد التعديل )

## جدول المحافظات (Governorate)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| name | CharField | اسم المحافظة |
| name_en | CharField | الاسم بالإنجليزية |
| code | CharField | كود المحافظة |
| region | CharField | المنطقة |
| created_at | DateTimeField | تاريخ الإنشاء |

## جدول المدن (City)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| name | CharField | اسم المدينة |
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
| city | ForeignKey | المدينة |
| address | TextField | العنوان |
| description | TextField | الوصف |
| capacity | PositiveIntegerField | السعة |
| price_per_hour | DecimalField | السعر للساعة |
| image | ImageField | الصورة الرئيسية |
| status | CharField | الحالة |
| features | JSONField | المميزات |
| services | ManyToManyField → HallService | قائمة الخدمات المتاحة لهذه القاعة |
| meals | ManyToManyField → HallMeal | قائمة الوجبات المتاحة لهذه القاعة |
| phone | CharField | الهاتف |
| email | EmailField | البريد الإلكتروني |
| website | URLField | الموقع الإلكتروني |
| latitude | DecimalField | خط العرض |
| longitude | DecimalField | خط الطول |
| created_at | DateTimeField | تاريخ الإنشاء |
| updated_at | DateTimeField | تاريخ التحديث |

## جدول خدمات القاعة (HallService)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| hall | ForeignKey | القاعة المرتبطة |
| name | CharField | اسم الخدمة |
| description | TextField | وصف الخدمة |
| price | DecimalField | سعر الخدمة |
| is_available | BooleanField | متاحة؟ |
| created_at | DateTimeField | تاريخ الإضافة |

## جدول وجبات القاعة (HallMeal)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| hall | ForeignKey | القاعة المرتبطة |
| name | CharField | اسم الوجبة |
| description | TextField | وصف الوجبة |
| price_per_unit | DecimalField | سعر الوحدة |
| is_vegetarian | BooleanField | نباتية؟ |
| is_available | BooleanField | متاحة؟ |
| images | listimages| ر الصور |
| created_at | DateTimeField | تاريخ الإضافة |

## جدول صور القاعات (HallImage)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| hall | ForeignKey | القاعة |
| image | ImageField | الصورة |
| image_type | CharField | نوع الصورة |
| title | CharField | عنوان الصورة |
| description | TextField | وصف الصورة |
| is_featured | BooleanField | صورة مميزة |
| order | PositiveIntegerField | ترتيب العرض |
| uploaded_at | DateTimeField | تاريخ الرفع |

## جدول الحجوزات (Booking)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| booking_id | UUIDField | معرف الحجز |
| hall | ForeignKey | القاعة |
| user | ForeignKey | المستخدم |
| customer_name | CharField | اسم العميل |
| customer_email | EmailField | بريد العميل |
| customer_phone | CharField | هاتف العميل |
| event_title | CharField | عنوان الحدث |
| event_description | TextField | وصف الحدث |
| start_datetime | DateTimeField | وقت البداية |
| end_datetime | DateTimeField | وقت النهاية |
| attendees_count | PositiveIntegerField | عدد الحضور |
| selected_services | ManyToManyField → HallService | الخدمات المختارة للحجز |
| selected_meals | ManyToManyField → HallMeal | الوجبات المختارة للحجز |
| total_price | DecimalField | السعر الإجمالي |
| status | CharField | حالة الحجز |
| admin_notes | TextField | ملاحظات الإدارة |
| created_at | DateTimeField | تاريخ الإنشاء |
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
| phone | CharField | الهاتف |
| subject | CharField | الموضوع |
| message | TextField | الرسالة |
| created_at | DateTimeField | تاريخ الإرسال |
| is_read | BooleanField | مقروءة |

## جدول الإشعارات (Notification)
| الحقل | النوع | الوصف |
|-------|-------|---------|
| id | AutoField | المعرف الفريد |
| user | ForeignKey | المستخدم |
| booking | ForeignKey | الحجز |
| notification_type | CharField | نوع الإشعار |
| title | CharField | العنوان |
| message | TextField | الرسالة |
| is_read | BooleanField | مقروء |
| created_at | DateTimeField | تاريخ الإنشاء |

## العلاقات بين الجداول
1. City → Governorate: many-to-one
2. Hall → Category, Governorate, City: many-to-one
3. Hall → HallService, HallMeal: many-to-many (خدمات ووجبات مخصصة لكل قاعة)
4. Booking → Hall: many-to-one
5. Booking → HallService, HallMeal: many-to-many (الخدمات والوجبات المختارة)
6. HallImage → Hall: many-to-one
7. HallManager → User, Hall: one-to-one
8. Notification → User, Booking: many-to-one