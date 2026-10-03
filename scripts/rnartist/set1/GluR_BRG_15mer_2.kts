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
