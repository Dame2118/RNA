import io.github.fjossinet.rnartist.core.*

 rnartist {
    ss {
       vienna {
          file = "/home/user/RNA/scripts/rnartist/set1/5-HT2C_2.vienna"
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
             4 to 4
             6 to 6
             16 to 16
             25 to 25
             47 to 47
          }
       }
       color {
          value = "#FFFFFF"
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
       path = "/home/user/RNA/scripts/rnartist/set1"
    }
    svg {
       path = "/home/user/RNA/scripts/rnartist/set1"
    }
 }
