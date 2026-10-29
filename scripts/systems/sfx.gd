extends Node
## Autoload "Sfx": efeitos sonoros (pool de players) e musica com crossfade.

var _streams: Dictionary = {}
var _pool: Array[AudioStreamPlayer] = []
var _music: AudioStreamPlayer
var _music_name := ""
var _music_token := 0
var sfx_volume_db := 0.0
var music_volume_db := -8.0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in 14:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_pool.append(p)
	_music = AudioStreamPlayer.new()
	_music.volume_db = -80.0
	add_child(_music)

func _load_stream(path: String) -> AudioStream:
	if _streams.has(path):
		return _streams[path] as AudioStream
	if not ResourceLoader.exists(path):
		return null
	var s := load(path) as AudioStream
	_streams[path] = s
	return s

func play(sfx_name: String, vol_db: float = 0.0, pitch: float = 1.0, jitter: float = 0.05) -> void:
	var s := _load_stream("res://assets/audio/%s.wav" % sfx_name)
	if s == null:
		return
	var chosen: AudioStreamPlayer = null
	for p in _pool:
		if not p.playing:
			chosen = p
			break
	if chosen == null:
		chosen = _pool[0]
	chosen.stream = s
	chosen.volume_db = vol_db + sfx_volume_db
	chosen.pitch_scale = maxf(0.1, pitch * (1.0 + randf_range(-jitter, jitter)))
	chosen.play()

func play_music(track: String, fade: float = 1.6) -> void:
	if track == _music_name:
		return
	_music_name = track
	_music_token += 1
	var token := _music_token
	var tw := create_tween()
	tw.tween_property(_music, "volume_db", -80.0, fade * 0.5)
	await tw.finished
	if token != _music_token:
		return
	if track == "":
		_music.stop()
		return
	var s := _load_stream("res://assets/audio/%s.ogg" % track)
	if s == null:
		return
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = true
	_music.stream = s
	_music.play()
	var tw2 := create_tween()
	tw2.tween_property(_music, "volume_db", music_volume_db, fade * 0.5)

func stop_music(fade: float = 2.0) -> void:
	play_music("", fade)
