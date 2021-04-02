import os
import psycopg2

CONNECTION_VARS = {
    'user': os.environ['DATABASE_USER'],
    'password': os.environ['DATABASE_PASS'],
    'host': os.environ['DATABASE_HOST'],
    'dbname': os.environ['DATABASE_NAME']
}


def create_webhooks_table():
    conn = psycopg2.connect(**CONNECTION_VARS)
    c = conn.cursor()
    c.execute('CREATE TABLE webhooks (id int, token text)')
    conn.commit()
    conn.close()


def get_webhooks():
    conn = psycopg2.connect(**CONNECTION_VARS)
    c = conn.cursor()
    c.execute('SELECT * FROM webhooks')
    results = c.fetchall()
    conn.close()
    return results


def delete_webhook(webhook_id, webhook_token):
    conn = psycopg2.connect(**CONNECTION_VARS)
    c = conn.cursor()
    q = (webhook_id, webhook_token,)
    c.execute('DELETE FROM webhooks WHERE webhook_id=%s AND webhook_token=%s', q)
    conn.commit()
    conn.close()
