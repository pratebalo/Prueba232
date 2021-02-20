import psycopg2
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")


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


def update_data(data):
    query = f"""set DateStyle='ISO, DMY';
        UPDATE data
        SET ultimo_mensaje='{data.ultimo_mensaje}', total_mensajes={data.total_mensajes}, sticker={data.sticker}, gif={data.gif}
        WHERE id={data.id};"""
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


def insert_tarea(tarea):
    query = f"""set DateStyle='ISO, DMY';
        INSERT INTO tareas
        (descripcion, personas, fecha, creador)
        VALUES ( '{tarea.descripcion}', ARRAY{list(map(int, tarea.personas))}, '{tarea.fecha}',{tarea.creador});"""
    connect(query)


def update_tarea(tarea):
    query = f"""set DateStyle='ISO, DMY';
        UPDATE tareas
        SET(descripcion, personas, fecha, creador, completada) =
        ( '{tarea.descripcion}', ARRAY{list(map(int, tarea.personas))}, '{tarea.fecha}',{tarea.creador},{tarea.completada})
        WHERE id = {tarea.id};"""
    connect(query)


def insert_lista(lista):
    query = f"""set DateStyle='ISO, DMY';
        INSERT INTO listas
        (nombre, elementos, tipo_elementos, fecha, creador, mensaje_id)
        VALUES ( '{lista.nombre}', ARRAY{lista.elementos}, ARRAY{list(map(int, lista.tipo_elementos))}, '{lista.fecha}',{lista.creador}), {lista.id_mensaje};"""
    connect(query)


def update_lista(lista):
    query = f"""set DateStyle='ISO, DMY';
        UPDATE listas
        SET (nombre, elementos, tipo_elementos, fecha, creador, id_mensaje) =
        ( '{lista.nombre}', ARRAY{lista.elementos}, ARRAY{list(map(int, lista.tipo_elementos))}, '{lista.fecha}',{lista.creador}, {lista.id_mensaje})
        WHERE id = {lista.id};"""
    connect(query)


def insert_bote(persona, cantidad, total, motivo):
    query = f"""set DateStyle='ISO, DMY';
    INSERT INTO botes
        (persona, cantidad, total, motivo)
         VALUES ({persona}, {cantidad}, {total}, '{motivo}');"""

    connect(query)


def insert_gastos(id, motivo, cantidad, fecha, nombre):
    query = f"""set DateStyle='ISO, DMY';
    INSERT INTO gastos    
    (id_persona, motivo, cantidad, fecha, nombre)
         VALUES ({id}, '{motivo}', {cantidad}, {fecha}, {nombre});"""

    connect(query)


def update_gasto(id_gasto):
    query = f"""
        UPDATE gastos
        SET pagado = True
        WHERE id = {id_gasto};"""
    connect(query)


def connect(query):
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()
    connection.close()
