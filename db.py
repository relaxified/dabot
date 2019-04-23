import sqlite3


def create_table():
    conn = sqlite3.connect("discord")
    c = conn.cursor()
    c.execute('''CREATE TABLE roles (channel_id int, message_id int, emoji_id int, emoji_name text)''')
    conn.commit()
    conn.close()


def insert(guild_id, message_id, role_id, emoji):
    conn = sqlite3.connect("discord")
    c = conn.cursor()
    c.execute("INSERT INTO role_reactions VALUES (?, ?, ?, ?)", (guild_id, message_id, role_id, emoji))
    conn.commit()
    conn.close()


def retrieve(guild_id, message_id):
    conn = sqlite3.connect("discord")
    c = conn.cursor()
    query = (guild_id, message_id,)
    c.execute("SELECT * FROM role_reactions WHERE guild_id=? AND message_id=?", query)
    result = c.fetchone()
    conn.close()
    return result



