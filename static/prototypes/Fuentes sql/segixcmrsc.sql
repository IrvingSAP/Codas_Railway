--------------------------------------------------------------------
-- NOMBRE DE SCRIPT....: SEGIXCMRSC                               --
-- DESCRIPCIÓN.........: INDICE SOBRE ARCHIVO SEGFFCMRSC          --
--                       POR EL CAMPO FECHCONSUL - FECHA CONSULTA --
-- TIPO OBJETO.........: INDEX                                    --
-- REQUERIMIENTO.......: SEG - INDICE SOBRE ARCHIVO SEGFFCMRSC    --
-- SUBDOMINIO..........: MODERNIZACIÓN DE LA TECNOLOGÍA.          --
-- FECHA DE CREACIÓN...: AGOSTO DE 2020                           --
-- AUTOR...............: ANDRES RIVERA CARVAJAL - PERSONAL SOFT   --
-- BASE DE DATOS RELACIONAL:  DB2 FOR  I                          --
--------------------------------------------------------------------
-- MODIFICACIONES:                                                --
-- FECHA DE MODIFICACIÓN :                                        --
-- AUTOR...............  :                                        --
-- DESCRIPCIÓN ......... :                                        --
-- REQUERIMIENTO.........:                                        --
--------------------------------------------------------------------

 -- CREATE INDEX &LIB.SEGIXCMRSC ON &LIB.SEGFFCMRSC
 CREATE INDEX &LIB.SEGIXCMRSC ON &LIB.SEGFFCMRSC
        (FECHCONSUL);
 LABEL ON INDEX &LIB.SEGIXCMRSC IS
       'Indice por fecha de consulta';
 COMMENT ON INDEX &LIB.SEGIXCMRSC IS
	      'Indice por fecha de consulta';
