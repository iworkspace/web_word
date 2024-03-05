大量小文文件创建

发音链接为
<div data-src-mp3="/media/english/uk_pron/a/acc/accom/accommodation__gb_2.mp3" data-src-ogg="/media/english/uk_pron_ogg/a/acc/accom/accommodation__gb_2.ogg" class="sound audio_play_button icon-audio pron-uk"> </div>

解压获取完整词典文件
7z e stardict.7z
python -c 'import stardict;stardict.convert_dict("stardict.db","stardict.csv")'

更新verbose
python -c 'import web_words;db=web_words.web_words();db.get_backlog_meta()'
