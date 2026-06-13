--------------------------------------------------------------------
-- NOMBRE DE SCRIPT....: SEGIXCMRS1                               --
-- DESCRIPCIÓN.........: INDICE SOBRE ARCHIVO SEGFFCMRSC          --
--                       POR IND CAMB SIMCARD Y FECHA DE CONSULTA.--
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

 -- CREATE INDEX &LIB.SEGIXCMRS1 ON &LIB.SEGFFCMRSC
 CREATE INDEX &LIB.SEGIXCMRS1 ON &LIB.SEGFFCMRSC
        (INDCAMBIO ASC, FECHCONSUL ASC) UNIT ANY KEEP IN MEMORY NO;
 LABEL ON INDEX &LIB.SEGIXCMRS1 IS
       'INDICE POR IND CAMB SIMCARD Y FECHA DE CONSULTA';
 COMMENT ON INDEX &LIB.SEGIXCMRS1 IS
       'INDICE POR IND CAMB SIMCARD Y FECHA DE CONSULTA';
