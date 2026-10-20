import io.github.fjossinet.rnartist.core.*

 rnartist {
    ss {
       vienna {
          file = "/home/user/RNA/scripts/dms/5-HT2C_2_dms.vienna"
       }
    }
    data {
       3 to 0.0081
       4 to 0.8737
       5 to 0.0077
       6 to 0.0297
       7 to 0.027
       8 to 0.0237
       9 to 9.0E-4
       10 to 0.0501
       11 to 0.026
       12 to 1.0E-4
       13 to 0.0267
       14 to 0.0433
       15 to 0.0284
       16 to 0.0541
       17 to 8.0E-4
       18 to 0.0282
       19 to 0.0065
       20 to 0.0253
       21 to 0.0067
       22 to 0.0263
       23 to 0.0297
       24 to 0.0069
       25 to 0.0131
       26 to 0.0087
       27 to 0.0013
       28 to 0.0503
       29 to 0.0193
       30 to 0.0298
       31 to 0.0036
       32 to 0.0216
       33 to 0.8056
       34 to 0.9182
       35 to 0.6611
       36 to 0.0201
       37 to 0.0176
       38 to 0.0254
       39 to 0.7026
       40 to 0.0353
       41 to 0.0073
       42 to 0.0478
       43 to 0.0052
       44 to 0.0211
       45 to 0.0405
       46 to 0.0132
       47 to 0.0305
       48 to 0.0156
       49 to 0.0147
       50 to 0.0018
       51 to 0.0211
       52 to 0.059
       53 to 0.0356
       54 to 0.0236
       55 to 0.0151
       56 to 0.0589
       57 to 0.8353
       58 to 0.7198
       59 to 0.007
       60 to 0.0286
       61 to 0.7389
       62 to 0.0081
       63 to 0.0287
       64 to 3.0E-4
       65 to 0.0246
       66 to 0.0222
       67 to 0.0485
       68 to 0.0168
       69 to 0.0017
       70 to 0.0171
       71 to 0.012
       72 to 0.7024
       73 to 0.0107
    }
    theme {
       details {
          value = 5
       }
       color {
          value = "#E8E8E8"
          type = "G"
       }
       color {
          value = "#E8E8E8"
          type = "U"
       }
       color {
          value = "#FFF3C4"
          to = "#B2182B"
          data between 0.0..0.9182
          type = "A"
       }
       color {
          value = "#FFF3C4"
          to = "#B2182B"
          data between 0.0..0.9182
          type = "C"
       }
       color {
          value = "#1A1A1A"
          type = "n"
       }
       color {
          value = "#0B5FFF"
          type = "n"
          location {
             4 to 4
             6 to 6
             16 to 16
             25 to 25
             47 to 47
          }
       }
    }
    layout {
       branch {
          location {
             4 to 4
             72 to 72
          }
          value = 0.0
       }
       junction {
          out_ids = "n"
          radius = 21.17
          location {
             3 to 5
             71 to 73
          }
       }
       junction {
          out_ids = "n"
          radius = 27.85
          location {
             14 to 15
             56 to 62
          }
       }
    }
    png {
       path = "/home/user/RNA/scripts/dms"
    }
    svg {
       path = "/home/user/RNA/scripts/dms"
    }
 }
