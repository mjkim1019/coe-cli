class BasePrompts:
    main_system = """"""
    example_messages = []
    files_content_prefix = """I have *added these files to the chat* so you see all of their contents. *Trust this message as the true contents of the files!* Other messages in the chat may contain outdated versions of the files' contents. """
    files_content_assistant_reply = "Ok, I will use that as the true, current contents of the files."
    system_reminder = """"""
