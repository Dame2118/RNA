rnartist {
  svg { path = "out" }
  ss { bn { seq = "CUUAUGAAAAUUUCAAGCAGUUCAAGCACUGUGGCUAUCCCUGGCUACACCUUCACAAGCCCGGGGAUGACCACCACCCUACUAGAGACAGUGUUUCACCAUGUCAGCCAGGCUGGUCUUGAACUCCUGACCUCGGGUGAUCUGCCCACCUUGGCCUCCCAAAGUGCUGGGAUUACAGCGUCAUCGGUUAUCUCGCAAAG" ; value = "..................(((((.((((((((((.(((((((((((...........)).))))))))).))))(((((.....(((.(((.((((.((((.(((.....)))))))...))))..)))..))))))))....(((......))).......)))))).)))))...(((.............)))...." ; name = "PODXL_200nt" } }
  theme {
    details { value = 5 }
    color { type = "N" ; value = "#D9D9D9" }   // all residue shapes neutral grey
    color { type = "n" ; value = "#222222" }   // all residue letters (ACGU) dark
    color {                                       // A edit-site shapes -> red
      type = "N" ; value = "red"
      location {
          98 to 98
      }
    }
    color {                                       // edit-site letters -> white for contrast
      type = "n" ; value = "white"
      location {
          98 to 98
      }
    }
  }
}

rnartist {
  svg { path = "out" }
  ss { bn { seq = "CCACUUCGACGCAUCCUGUGGCCACCCCAACAAGCUCGGGACAUGACCAUCUUAUGAAAAUUUCAAGCAGUUCAAGCACUGUGGCUAUCCCUGGCUACACCUUCACAAGCCCGGGGAUGACCACCACCCUACUAGAGACAGUGUUUCACCAUGUCAGCCAGGCUGGUCUUGAACUCCUGACCUCGGGUGAUCUGCCCACCUUGGCCUCCCAAAGUGCUGGGAUUACAGCGUCAUCGGUUAUCUCGCAAAGAACUCAACAGACCUCCAGUCAGAUGCCAGCCAGCUCUACGGCCCCUUCCU" ; value = ".......(((((.......(((((.(((.........))).(((((.....)))))......(((.(.((((((((....((((.(((((((((((...........)).))))))))).))))..........(((((...)))))((((.(((.....)))))))))))))))).)))....(((((.......))))))))))(((((......))))).....)))))...(((.((((.((...((..((....))..))..)).))))))).(((........)))........" ; name = "PODXL_300nt" } }
  theme {
    details { value = 5 }
    color { type = "N" ; value = "#D9D9D9" }   // all residue shapes neutral grey
    color { type = "n" ; value = "#222222" }   // all residue letters (ACGU) dark
    color {                                       // A edit-site shapes -> red
      type = "N" ; value = "red"
      location {
          148 to 148
      }
    }
    color {                                       // edit-site letters -> white for contrast
      type = "n" ; value = "white"
      location {
          148 to 148
      }
    }
  }
}
