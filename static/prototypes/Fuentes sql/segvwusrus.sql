-------------------------------------------------------------------------------
-- Descripcion.........: VISTA DE JOURNAL PARA LA CREACION DE USUARIO POR USM--          --
-- Tipo Objeto.........: Vista                                               --
-- Requerimiento.......: PMO31385-Creacion de usuario                        --
-- Subdominio..........: Transversales Iseries                               --
-- Fecha De Creacion...: Enero 20-2022                                   --
-- Autor...............: Carlos Rojas - Bancolombia                          --
-- Base de datos relacional:  DB2 for i                                      --
-------------------------------------------------------------------------------
-- MODIFICACIONES:                                                           --
-- Fecha de Modificacion :                                                   --
-- Autor...............  :                                                   --
-- Descripcion ......... :                                                   --
-- Requerimiento.........:                                                   --
-------------------------------------------------------------------------------

-- Creando la tabla &LIB/SEGVWUSRUS
 CREATE OR REPLACE VIEW &LIB.SEGVWUSRUS AS SELECT SEQUENCE_NUMBER,
 SUBSTR(CAST(PATH_NAME AS VARCHAR(100)),26) AS PN FROM
 TABLE(QSYS2.DISPLAY_JOURNAL('&LIB', 'SEGJRNCUSR')) AS JT
 WHERE JOURNAL_ENTRY_TYPE = 'JT';

