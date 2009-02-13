from django.core.management import execute_from_command_line
import conf

conf.configure_django(INSTALLED_APPS=('ddb', 'ddb.test'))

if __name__ == "__main__":
    execute_from_command_line()

