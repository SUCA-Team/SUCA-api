# JMdict Database Dump Attribution

This file (`dump.sql`) contains a PostgreSQL database dump of the JMdict Japanese-English dictionary data.

## Copyright and License

**Copyright:** © Electronic Dictionary Research and Development Group (EDRDG)  
**License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)  
**License URL:** https://creativecommons.org/licenses/by-sa/4.0/

## Source

- **Project Homepage:** http://www.edrdg.org/
- **JMdict Download:** http://www.edrdg.org/jmdict/j_jmdict.html
- **License Details:** http://www.edrdg.org/edrdg/licence.html

## Citation

When using this data, please cite:

> EDRDG, "JMdict/EDICT Japanese-English Dictionary File",  
> Electronic Dictionary Research and Development Group,  
> http://www.edrdg.org/jmdict/j_jmdict.html

## Contents

This dump contains the following tables derived from JMdict XML:

- `entry` - Dictionary entries with JMdict sequence numbers
- `kanji` - Kanji spellings with metadata (keb, ke_inf, ke_pri)
- `reading` - Kana readings with metadata (reb, re_inf, re_pri)
- `sense` - Word meanings/senses with POS tags
- `gloss` - English definitions
- `example` - Usage examples (if present)
