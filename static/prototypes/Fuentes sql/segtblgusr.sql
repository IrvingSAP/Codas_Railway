------------------------------------------------------------
 SCRIPT....:SEGTBLGUSR
ON.........:Log de cambio de estado de usuarios
TO.........:TABLE.
ENTO.......:EVC00032-TRANSVERSALES ISERIES.
O..........:TRANSVERSALES DE APOYO ISERIES.
CREACION...:Noviembre-2023.
...........:Kevin Johance Gómez T.
------------------------------------------------------------
IONES
MODIFICACION.:
.............:
UN...........:
------------------------------------------------------------

de la tabla

E LIBRERIA DE TRABAJO
 SCHEMA &LIB;  --CREACION DE TABLA - LOG-CAMBIOS-USUARIOS

la tabla &LIB/SEGTBLGUSR
EPLACE TABLE &LIB/log_cambios_usuarios
TEM NAME SEGTBLGUSR(
O CHAR (10),
 CHAR (10),
HAR (15),
T CHAR (10),
T CHAR (10),
 CHAR (50),
 CHAR (50),
M NUMERIC (8),
M NUMERIC (6),
 CHAR (10),
 CHAR (1))

BLGUSR;

iendo el texto de etiqueta para &LIB/SEGTBLGUSR
BLE &LIB/SEGTBLGUSR
cambio de estado usuarios vacantes';


iendo las etiquetas de columna para &LIB/SEGTBLGUSR
LUMN &LIB/SEGTBLGUSR (

O TEXT IS 'Nombre de usuario',
 TEXT IS 'PROPIETARIO',
EXT IS 'Documento del usuario',
T TEXT IS 'Estado Anterior',
T TEXT IS 'Estado Actual',
 TEXT IS 'TEXTO ANTERIOR',
 TEXT IS 'TEXTO ACTUAL' ,
M TEXT IS 'FECHA DE CAMBIO',
M TEXT IS 'HORA DEL CAMBIO',
 TEXT IS 'Usuario de cambio',
 TEXT IS 'Estado cambio 1 = exito, 2 = error');


ciendo las cabeceras de columna para &LIB/SEGTBLGUSR

LUMN &LIB/SEGTBLGUSR (
O IS 'Nombre de usuario',
 IS 'PROPIETARIO',
S 'Documento del usuario',
T IS 'Estado Anterior',
T IS 'Estado Actual',
 IS 'TEXTO ANTERIOR',
  IS 'TEXTO ACTUAL',
M IS 'FECHA DE CAMBIO',
M IS 'HORA DEL CAMBIO',
  IS 'Usuario de cambio',
 IS 'Estado cambio 1 = exito, 2 = error');

