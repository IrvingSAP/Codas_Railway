--?* ?Archivo:?UZROPCMVW                                                    *
--?* ?Descripcion:Consulta opciones de menú.                              ?*
--?* Requerimiento consultas de menu para gaia web                       ?*
--?*                                                                      ?*
--?* ?Analista : Pedro Rodriguez Pimienta BVDPARREM - BankVision S.A.S      *
--?* ?Fecha    :?Junio 2021                                              *
--?* ?Empresa  :?BankVision S.A.S SoftWare                                  *
--?**************************************************************************
--  Generar SQL
--  Base de datos relacional:
--  Opción de estándares:          DB2 UDB iSeries
--?**************************************************************************
--?* ?Analista :                                    - BankVision S.A.S      *
--?* ?Fecha    :?                                                           *
--?* ?Empresa  :?                                                           *
--?* ?Descrip  :?                                                           *
--?**************************************************************************
--?*Se crea vista.

   CrEATE OR REPLACE VIEW &LIB.UZCNROPCMV AS
   SELECT DISTINCT * FROM (SELECT UCODBC UCODBC, XBNCOM UZDSBC,
   UCODAP UZCAPL, XFDESC UZDAPL,
   UTIPMN UZTPMN, C.U2DSST UZDTPM,
   USTPMN UZSTPM, CASE WHEN USTPMN = ' ' THEN ' '
   WHEN USTPMN <> ' ' THEN B.U2DSST END UZDSTM,
   UOPCIO UZOPME, SFDESC UZDOPN, sauser,
   CURRENT_SERVER SERVIDOR
   FROM VISIONSYSR.UMNU LEFT OUTER JOIN VISIONSYSR.SFUNC
   ON UFUNSI=SFFUNC
   LEFT OUTER JOIN VISIONSYSR.SAUTH ON UCODBC=SACOMP
   AND UFUNSI= SAFUNC
   LEFT OUTER JOIN VISIONSYSR.XBCOMP ON UCODBC = XBCCOM
   LEFT OUTER JOIN VISIONSPAR.XTCOD ON UCODAP = TRIM(XFMLCD)
   AND XFLDNM = 'APPL' AND XFAPCD = ' '
   LEFT OUTER JOIN VISIONSPAR.UMNU2 C ON UCODBC = C.U2ODBC
   AND UCODAP = C.U2ODAP and C.U2IPMN = UTIPMN AND C.U2TPMN = ' '
   LEFT OUTER JOIN VISIONSPAR.UMNU2 B ON UCODBC = B.U2ODBC
   AND UCODAP = B.U2ODAP and B.U2IPMN = UTIPMN AND B.U2TPMN = USTPMN
   left outer join &LIB/segffdsusr on (sauser=upuprf or sauser=UPGRPF or
   sauser=sUBSTR(UPSUPG,1,10) or
   sauser=sUBSTR(UPSUPG,11,10)  or sauser=sUBSTR(UPSUPG,21,10) or
   sauser=sUBSTR(UPSUPG,31,10)  or sauser=sUBSTR(UPSUPG,41,10) or
   sauser=sUBSTR(UPSUPG,51,10)  or sauser=sUBSTR(UPSUPG,61,10) or
   sauser=sUBSTR(UPSUPG,71,10)  or sauser=sUBSTR(UPSUPG,81,10) or
   sauser=sUBSTR(UPSUPG,91,10)  or sauser=sUBSTR(UPSUPG,101,10) or
   sauser=sUBSTR(UPSUPG,111,10) or sauser=sUBSTR(UPSUPG,121,10) or
   sauser=sUBSTR(UPSUPG,131,10) or sauser=sUBSTR(UPSUPG,141,10))
   WHERE sauser <> ' ') A;

