import io.github.fjossinet.rnartist.core.*

 rnartist {
    ss {
       vienna {
          file = "/home/user/RNA/scripts/rnartist/set1/AZIN1.vienna"
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
             31 to 31
          }
       }
       color {
          value = "#FFFFFF"
          type = "n"
          location {
             31 to 31
          }
       }
    }
    layout {
       branch {
          location {
             8 to 11
          }
          value = 0.0
       }
       junction {
          out_ids = "n"
          radius = 25.62
          location {
             7 to 12
             34 to 35
          }
       }
       junction {
          out_ids = "n"
          radius = 23.4
          location {
             16 to 19
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
