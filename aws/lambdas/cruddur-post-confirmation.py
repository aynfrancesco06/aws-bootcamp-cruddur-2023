import json
import psycopg2
import os

def lambda_handler(event, context):
    user = event['request']['userAttributes']
    print('userAttributes')
    print(user)

    user_display_name = user['name']
    user_email        = user['email']
    user_cognito_id   = user['sub']
    user_handle       = user['preferred_username']
    try:

        sql = f"""
        INSERT INTO public.users (
            display_name,
            email, 
            handle, 
            cognito_user_id
            ) 
        VALUES(%(display_name)s,%(email)s,%(handle)s,%(cognito_user_id)s)
        """ 
        print('-----SQL STATEMENT')
        print(sql)
        conn = psycopg2.connect(os.getenv('CONNECTION_URL'))
        cur = conn.cursor()
        params = {
            'display_name': user_display_name,
            'email': user_email,
            'cognito_user_id': user_cognito_id,
            'handle': user_handle
        }
        cur.execute(sql,params) 
        conn.commit() 
        print('execute end')

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        
    finally:
        if conn is not None:
            cur.close()
            conn.close()
            print('Database connection closed.')

    return event