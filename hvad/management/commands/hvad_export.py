import json
import os

import polib
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument('args', metavar='app_label[.ModelName]', nargs='*',
                            help='Restricts dumped data to the specified app_label or app_label.ModelName.')
        parser.add_argument('--locale', '-l', default=[], dest='locale', action='append',
                            help='Creates or updates the message files for the given locale(s) (e.g. pt_BR). '
                                 'Can be used multiple times.')

    def handle(self, *app_labels, **options):
        locale = options.get('locale')
        locales = locale

        for locale in locales:
            for label in app_labels:
                po = polib.POFile()
                Cls = apps.get_model(label)
                for cls_object in Cls.objects.language("en").all():
                    for field in cls_object._meta.translations_model._meta.fields:
                        if field.name not in ("master", "language_code", "id"):
                            val = getattr(cls_object, field.name)
                            if val == "":
                                continue
                            try:
                                translated_val = getattr(Cls.objects.language(locale).get(pk=cls_object.pk), field.name)
                            except Cls.DoesNotExist:
                                translated_val = ""
                            if val:
                                identifier = {'cls': Cls._meta.app_label + "." + str(Cls.__name__),
                                              'field_name': field.name,
                                              'pk': str(cls_object.pk)}
                                entry = polib.POEntry(comment=json.dumps(identifier),
                                                      msgid=val,
                                                      msgstr=translated_val)
                                po.append(entry)

                basepath = os.path.join(settings.LOCALE_PATHS[0], locale, "hvad")
                if not os.path.exists(basepath):
                    os.makedirs(basepath)
                po.save(os.path.join(basepath, "%s.po" % str(Cls.__name__)))
