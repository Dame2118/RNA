import io.github.fjossinet.rnartist.core.*

 rnartist {
    ss {
       vienna {
          file = "/home/user/RNA/scripts/rnartist/set2/LEAPER3_FLNA_50bp_AC_external_bulge.vienna"
       }
    }
    theme {
       details {
          value = 5
       }
       color {
          value = "#E8E8E8"
          type = "N"
       }
       color {
          value = "#222222"
          type = "n"
       }
       color {
          value = "#D62728"
          type = "N"
          location {
             15 to 15
          }
       }
       color {
          value = "#FFFFFF"
          type = "n"
          location {
             15 to 15
          }
       }
    }
    layout {
       branch {
          location {
             65 to 68
          }
          value = 0.0
       }
       junction {
          out_ids = "n"
          radius = 25.62
          location {
             40 to 41
             64 to 69
          }
       }
    }
    png {
       path = "/home/user/RNA/scripts/rnartist/set2"
    }
    svg {
       path = "/home/user/RNA/scripts/rnartist/set2"
    }
 }
