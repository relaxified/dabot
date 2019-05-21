import os
import psycopg2

CONNECTION_VARS = {
    'user': os.environ['DATABASE_USER'],
    'password': os.environ['DATABASE_PASS'],
    'host': 'ec2-23-23-110-26.compute-1.amazonaws.com',
    'dbname': 'da39rmke9ic877'
}


def create_table():
    conn = psycopg2.connect(**CONNECTION_VARS)
    c = conn.cursor()
    c.execute('CREATE TABLE role_reactions (guild_id int, message_id int, role_id int, emoji text)')
    conn.commit()
    conn.close()


def create_webhooks():
    conn = psycopg2.connect(**CONNECTION_VARS)
    c = conn.cursor()
    c.execute('CREATE TABLE webhooks (webhook_id int, webhook_token text)')
    conn.commit()
    conn.close()


def insert(guild_id, message_id, role_id, emoji):
    conn = psycopg2.connect(**CONNECTION_VARS)
    c = conn.cursor()
    q = (guild_id, message_id, role_id, emoji)
    c.execute('INSERT INTO role_reactions (guild_id, message_id, role_id, emoji) VALUES (%s, %s, %s, %s)', q)
    conn.commit()
    conn.close()


def retrieve(guild_id, message_id, emoji):
    conn = psycopg2.connect(**CONNECTION_VARS)
    c = conn.cursor()
    q = (guild_id, message_id, emoji,)
    c.execute('SELECT * FROM role_reactions WHERE guild_id=%s AND message_id=%s AND emoji=%s', q)
    result = c.fetchone()
    conn.close()
    return result


def get_webhooks():
    conn = psycopg2.connect(**CONNECTION_VARS)
    c = conn.cursor()
    c.execute('SELECT * FROM webhooks')
    results = c.fetchall()
    conn.close()
    return results


def del_webhook(webhook_id, webhook_token):
    conn = psycopg2.connect(**CONNECTION_VARS)
    c = conn.cursor()
    q = (webhook_id, webhook_token,)
    c.execute('DELETE FROM webhooks WHERE webhook_id=%s AND webhook_token=%s', q)
    conn.commit()
    conn.close()

