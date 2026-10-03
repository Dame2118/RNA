import io.github.fjossinet.rnartist.core.*

 rnartist {
    ss {
       vienna {
          file = "/home/user/RNA/scripts/rnartist/set2/GRIA2_R-G_1.vienna"
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
             6 to 6
          }
       }
       color {
          value = "#FFFFFF"
          type = "n"
          location {
             6 to 6
          }
       }
    }
    layout {
       branch {
          location {
             6 to 8
          }
          value = 0.0
       }
       junction {
          out_ids = "n"
          radius = 23.4
          location {
             5 to 9
             25 to 26
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
