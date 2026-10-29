shader_type canvas_item;

// Faz o sprite piscar em uma cor (usado no dano e na cura).
// O script Actor altera "flash" (0 a 1) e "flash_color".
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	COLOR = vec4(mix(c.rgb, flash_color.rgb, flash), c.a);
}
