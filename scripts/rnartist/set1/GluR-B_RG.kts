import io.github.fjossinet.rnartist.core.*

 rnartist {
    ss {
       vienna {
          file = "/home/user/RNA/scripts/rnartist/set1/GluR-B_RG.vienna"
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
             51 to 51
          }
          value = 0.0
       }
       junction {
          out_ids = "n"
          radius = 21.17
          location {
             5 to 7
             50 to 52
          }
       }
       junction {
          out_ids = "n"
          radius = 21.17
          location {
             15 to 17
             40 to 42
          }
       }
       junction {
          out_ids = "n"
          radius = 21.17
          location {
             19 to 21
             36 to 38
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
