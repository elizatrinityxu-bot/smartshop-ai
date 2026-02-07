graph TD
    User["User (Web Browser)"]

    User --> Django["Django Web Application"]

    Django --> MySQL["MySQL Database"]
    MySQL --> Django

    Django --> OpenAI["OpenAI API"]
    OpenAI --> Django

    Django --> User
