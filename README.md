Helpdesk system, developed for diplom project

change basic variables to your:

  .drone.yml file:
    12 line: git@github.com:user/project - to your user and project

  /helpdesk/helpdesk/settings.py:
    8 line: secret-key - to your secret-key for django project
    115 line: email_host - to your email host
    116 line: email_port - to your email port
    118 line: email_host_user - to your email host user
    119 line: email_host_password - to your email host password

  /helpdesk/desk/views.py:
    21 line: email_host_user - to your email host user
