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
          value = "#4A3AA7"
          type = "A"
       }
       color {
          value = "#FFFFFF"
          type = "a"
       }
       color {
          value = "#EDA100"
          type = "U"
       }
       color {
          value = "#1A1A1A"
          type = "u"
       }
       color {
          value = "#2A78D6"
          type = "G"
       }
       color {
          value = "#FFFFFF"
          type = "g"
       }
       color {
          value = "#1BAF7A"
          type = "C"
       }
       color {
          value = "#1A1A1A"
          type = "c"
       }
       color {
          value = "#E34948"
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
