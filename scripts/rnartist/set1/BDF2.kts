import io.github.fjossinet.rnartist.core.*

 rnartist {
    ss {
       vienna {
          file = "/home/user/RNA/scripts/rnartist/set1/BDF2.vienna"
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
             17 to 17
          }
       }
       color {
          value = "#FFFFFF"
          type = "n"
          location {
             17 to 17
          }
       }
    }
    layout {
       branch {
          location {
             8 to 8
             46 to 48
          }
          value = 0.0
       }
       junction {
          out_ids = "n"
          radius = 25.62
          location {
             7 to 9
             45 to 49
          }
       }
       junction {
          out_ids = "n"
          radius = 34.54
          location {
             16 to 21
             33 to 38
          }
       }
    }
    png {
       path = "/home/user/RNA/scripts/rnartist/set1"
    }
    svg {
       path = "/home/user/RNA/scripts/rnartist/set1"
    }
 }
