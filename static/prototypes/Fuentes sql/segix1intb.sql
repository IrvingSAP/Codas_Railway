-- *?*===================================================================     *
-- *?*  (C) Copyright 2020 Bancolombia                                        *
-- *?*===================================================================     *
-- *  Script:  ?SEGIX1INTB                                                    *
-- *  Descripcion:SEG-Tablas Inscritas Consulta a IFS y envio correo  M     ?*
-- *                                                                  ón    ?*
-- *                                                                        ?*
-- *                                                                         ?*
-- *  Autor:?JOSE RICARDO YUMAYUSA GUALTEROS                                  *
-- *  Empresa:?TCS                                                            *
-- *  Fecha Creacion:?09 - Junio 2020                                         *
-- *?**************************************************************************

--   ?Creando los Indices para &LIB/SEGTBINSTB

CREATE UNIQUE INDEX &LIB/Tablas_Inscritas_Consulta_a_IFS_Lib_Tab
FOR SYSTEM NAME SEGIX1INTB (
  ON &LIB/Tablas_Inscritas_Consulta_a_IFS
     ( NOMBRE_LIBRERIA, NOMBRE_TABLA ) ;

--LABEL ON INDEX &LIB/SEGIX1INTB
LABEL ON INDEX &LIB/Tablas_Inscritas_Consulta_a_IFS_Lib_Tab
   IS 'Tablas Inscritas Consulta a IFS Lib-Tab';

--COMMENT ON &LIB/SEGIX1INTB
COMMENT ON INDEX &LIB/Tablas_Inscritas_Consulta_a_IFS_Lib_Tab
   IS 'Tablas Inscritas Consulta a IFS Lib-Tab';

