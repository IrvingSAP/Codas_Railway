-- ********************************************************************* *
-- NOMBRE DE CROGRAMA..: SEGTBUSRIN                                      *
-- DESCRIPCIÓN.........: ARCHIVO DE INSUMO TEMPORAL                      *
--                     : CONTIENE LA INFORMACION DE USM, PARA VALIDAR LA *
--                     : CREACION DE USUARIO AUTOMATICA                  *
--********************************************************************   *
-- REQUERIMIENTO.......: PMO25818 - CREACION USUARIOS ISERIES            *
-- SUBDOMINIO..........: RIESGOS Y SEGURIDAD                             *
-- FECHA DE CREACIÓN...: 28 DE ENERO DE 2022.                            *
-- AUTOR...............: CARLOS ROJAS.                                   *
-- ***********************************************************************
--  /* REGISTRO Y CAMPOS */

 CREATE OR REPLACE TABLE &LIB.InsumoCreacionUsuario
                        FOR SYSTEM NAME SEGTBUSRIN(
 Renglon                FOR COLUMN NRORENGLON CHAR(10)
                                   CCSID 284 NOT NULL DEFAULT ' ',
 Numero_Usm             FOR COLUMN NUMEROUSM CHAR(10)
                                   CCSID 284 NOT NULL DEFAULT ' ',
 Fecha_Pedido           FOR COLUMN FECHAPED  Char(10)
                                   CCSID 284 NOT NULL DEFAULT ' ',
 Usuario_Red            FOR COLUMN USUARIRED   Char(10)
                                   CCSID 284 NOT NULL DEFAULT ' ',
 Identificacion         FOR COLUMN NUMIDENTI   Char(10)
                                   CCSID 284 NOT NULL DEFAULT ' ',
 Maquina                FOR COLUMN MAQUINAL   Char(20)
                                   CCSID 284 NOT NULL DEFAULT ' ',

 Correo_Usuario         FOR COLUMN CORREOUSR   Char(100)
                                   CCSID 284 NOT NULL DEFAULT ' ',
 CONSTRAINT &LIB.Renglon_PK
 PRIMARY KEY (Renglon))
 RCDFMT   RSEGTBUSRI;

LABEL ON TABLE rtclibcjr.SEGTBUSRIN Is
'Seg - Creacion Usuario x Usm - Insumo';

LABEL ON  rtclibcjr.SEGTBUSRIN(
Renglon                 Text Is 'Renglon o consecutivo........',
Numero_Usm              Text Is 'ID Reglas usuarios...........',
Fecha_Pedido            Text Is 'Codigo de la Regla...........',
Usuario_Red             Text Is 'Estado.......................',
Identificacion          Text Is 'Nombre de Usuario............',
Maquina                 Text Is 'Maquina......................',
Correo_Usuario          Text Is 'Fecha Creacio................');
