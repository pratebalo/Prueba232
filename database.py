import psycopg2
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")


def insert_lista(lista):
    query = f"""set DateStyle='ISO, DMY';
        INSERT INTO listas
        (nombre, elementos, tipo_elementos, fecha, creador)
        VALUES ( '{lista.nombre}', ARRAY{lista.elementos}, ARRAY{list(map(int, lista.tipo_elementos))}, '{lista.fecha}',{lista.creador});"""
    connect(query)


def insert_tarea(tarea):
    query = f"""set DateStyle='ISO, DMY';
        INSERT INTO tareas
        (descripcion, personas, fecha, creador)
        VALUES ( '{tarea.descripcion}', ARRAY{list(map(int, tarea.personas))}, '{tarea.fecha}',{tarea.creador});"""
    connect(query)


def insert_conversacion(id, mensaje_id, nombre):
    query = f"""INSERT INTO conversaciones
                (id, mensaje_id,nombre, total_mensajes)
                VALUES ({id},{mensaje_id},'{nombre}',{0});"""

    connect(query)


def update_conversacion(conversacion):
    query = f"""
        UPDATE  conversaciones
        SET
            total_mensajes ={conversacion.total_mensajes},
            mensaje_id = {conversacion.mensaje_id}
        WHERE id={conversacion.id};"""
    connect(query)


def select(table):
    query = f"SELECT * FROM {table}"
    connection = psycopg2.connect(DATABASE_URL)
    result = pd.read_sql(query, connection).sort_values(by="id", ignore_index=True)
    connection.close()
    return result


def delete(table, id):
    query = f"""DELETE FROM {table}
            WHERE ID = {id}
            RETURNING *;"""
    connection = psycopg2.connect(DATABASE_URL)
    result = pd.read_sql(query, connection)
    connection.commit()
    connection.close()
    return result


def update_tarea(tarea):
    query = f"""set DateStyle='ISO, DMY';
        INSERT INTO tareas
        (descripcion, personas, fecha, creador)
        VALUES ( '{tarea.descripcion}', ARRAY{list(map(int, tarea.personas))}, '{tarea.fecha}',{tarea.creador})
        WHERE id = {tarea.id};"""
    connect(query)


def update_lista(lista):
    query = f"""set DateStyle='ISO, DMY';
        UPDATE listas
        SET (nombre, elementos, tipo_elementos, fecha, creador) =
        ( '{lista.nombre}', ARRAY{lista.elementos}, ARRAY{list(map(int, lista.tipo_elementos))}, '{lista.fecha}',{lista.creador})
        WHERE id = {lista.id};"""
    connect(query)


def update_data(data):
    query = f"""set DateStyle='ISO, DMY';
        UPDATE data
        SET ultimo_mensaje='{data.ultimo_mensaje}', total_mensajes={data.total_mensajes}, sticker={data.sticker}
        WHERE id={data.id};"""
    connect(query)


def insert_bote(persona,cantidad,total,motivo):
    query = f"""INSERT INTO bote
        (persona, cantidad, total, motivo)
         VALUES ({persona}, {cantidad}, {total}, '{motivo}');"""

    connect(query)


def insert_gastos(persona, motivo, cantidad):
    query = f"""INSERT INTO gastos    
    (persona, motivo, cantidad, fecha)
         VALUES ({persona}, '{motivo}', {cantidad});"""

    connect(query)


def connect(query):
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()
    connection.close()
