-----------------------------------------------------------------------------
-- Descripcion.........: Archivo Informe para CPYFRMSTR de IFS USM           --
-- Tipo Objeto.........: TABLE                                               --
-- Requerimiento.......: PMO31385-Creacion de usuario                        --
-- Subdominio..........: Transversales Iseries                               --
-- Fecha De Creacion...: Diciembre 15-2021                                   --
-- Autor...............: Carlos Rojas - Bancolombia                          --
-- Base de datos relacional:  DB2 for i                                      --
-------------------------------------------------------------------------------
-- MODIFICACIONES:                                                           --
-- Fecha de Modificacion :                                                   --
-- Autor...............  :                                                   --
-- Descripcion ......... :                                                   --
-- Requerimiento.........:                                                   --
-------------------------------------------------------------------------------

CREATE OR REPLACE TABLE &LIB.ArchivoInformeUsuarioIfsUsm
                        FOR SYSTEM NAME SEGTBUSRUS(
ID_USM                  FOR COLUMN IDUSM    VARCHAR ( 10)  NOT NULL ,
FECHA                   FOR COLUMN FECHAP   VARCHAR ( 10)  NOT NULL ,
USUARIO                 FOR COLUMN USRUSM   VARCHAR ( 10)  NOT NULL ,
IDENTIFICACION          FOR COLUMN IDENTIFI VARCHAR ( 10)  NOT NULL ,
PLATAFORMA              FOR COLUMN PLATAF   VARCHAR ( 20)  NOT NULL ,
CONSTRAINT &LIB.ID_USM_PK
  PRIMARY KEY (ID_USM))
RCDFMT FMTTBIMPUS;

-- Estableciendo eL texto de etiqueta para &LIB/SEGTBIMPUS
LABEL ON TABLE &LIB.SEGTBUSRUS
   IS 'Archivo Informe para CPYFRMSTR de IFS USM';

LABEL ON  &LIB.SEGTBUSRUS(
ID_USM              Text Is 'Id USM ...........................',
FECHA               Text Is 'Fecha Proceso.....................',
USUARIO             Text Is 'Usuario de Red....................',
IDENTIFICACION      Text Is 'Identificacion o Cedula...........',
PLATAFORMA          Text Is 'Plataforma........................'
);
