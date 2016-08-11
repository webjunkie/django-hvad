import glob
import json
import os

import polib
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument('--locale', '-l', default=[], dest='locale', action='append',
                            help='Creates or updates the message files for the given locale(s) (e.g. pt_BR). '
                                 'Can be used multiple times.')

    def handle(self, *app_labels, **options):
        locale = options.get('locale')

        locale_dirs = filter(os.path.isdir, glob.glob('%s/*' % settings.LOCALE_PATHS[0]))

        for locale_dir in locale_dirs:
            lang = os.path.split(locale_dir)[-1]

            if locale and lang not in locale:
                continue

            path = os.path.join(locale_dir, "hvad")
            if not os.path.exists(path):
                continue

            locale_files = glob.glob('%s/*' % path)
            for f in locale_files:
                po = polib.pofile(f)

                for entry in po:
                    identifier = json.loads(entry.comment)
                    cls = identifier['cls']
                    Cls = apps.get_model(cls)
                    if entry.msgstr != "":
                        defaults = {identifier['field_name']: entry.msgstr}
                        try:
                            _m, created = Cls.objects.translations_model.objects.update_or_create(
                                master_id=identifier['pk'],
                                language_code=lang,
                                defaults=defaults)
                            print "created" if created else "updated", identifier
                        except IntegrityError:
                            print "skipped", identifier
