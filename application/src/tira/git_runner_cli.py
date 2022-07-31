import os
import django
    
def main():
    """Run git_runner via cli.
       Later this will become a fully fledged cli tool that we use as wrapper in the repository.
       At the moment, we just execute some predefined commands
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_admin.settings')
    django.setup()
    from tira.git_runner import create_user_repository, create_task_repository
    
    #print("Create user repository")
    #create_user_repository('delete-me-maik-22')
    create_task_repository('delete-me-maik-223')

if __name__ == '__main__':
    main()

