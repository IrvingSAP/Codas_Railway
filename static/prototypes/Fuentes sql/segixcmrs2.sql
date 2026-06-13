--------------------------------------------------------------------
-- NOMBRE DE SCRIPT....: SEGIXCMRS2                               --
-- DESCRIPCIÓN.........: INDICE SOBRE ARCHIVO SEGFFCMRSC          --
--                       POR CÓDIGO RESPUESTA.                    --
-- TIPO OBJETO.........: INDEX                                    --
-- REQUERIMIENTO.......: SEG - INDICE SOBRE ARCHIVO SEGFFCMRSC    --
-- SUBDOMINIO..........: MODERNIZACIÓN DE LA TECNOLOGÍA           --
-- FECHA DE CREACIÓN...: NOVIEMBRE DE 2020                        --
-- AUTOR...............: ANDRES RIVERA CARVAJAL - PERSONALSOFT    --
-- BASE DE DATOS RELACIONAL:  DB2 FOR I                           --
--------------------------------------------------------------------
-- MODIFICACIONES:                                                --
-- FECHA DE MODIFICACIÓN :                                        --
-- AUTOR...............  :                                        --
-- DESCRIPCIÓN ......... :                                        --
-- REQUERIMIENTO.........:                                        --
--------------------------------------------------------------------

 -- CREATE INDEX &LIB.SEGIXCMRS2 ON &LIB.SEGFFCMRSC
 CREATE INDEX &LIB.SEGIXCMRS2 ON &LIB.SEGFFCMRSC
        (CODIGORES ASC) UNIT ANY KEEP IN MEMORY NO;
 LABEL ON INDEX &LIB.SEGIXCMRS2 IS
       'INDICE POR CÓDIGO RESPUESTA';
 COMMENT ON INDEX &LIB.SEGIXCMRS2 IS
       'INDICE POR CÓDIGO RESPUESTA';
