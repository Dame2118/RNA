import io.github.fjossinet.rnartist.core.*

 rnartist {
    ss {
       vienna {
          file = "/home/user/RNA/scripts/rnartist/set1/GluR_BRG_15mer_2.vienna"
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
             6 to 6
             29 to 29
          }
          value = 0.0
       }
       junction {
          out_ids = "n"
          radius = 21.17
          location {
             5 to 7
             28 to 30
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
