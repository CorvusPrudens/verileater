#ifndef EATER_DISPLAY_H
#define EATER_DISPLAY_H

#include <cstdint>
#include <GL/glew.h>
#include <GLFW/glfw3.h>

#include <vector>

struct Vector {
    int x;
    int y;
};

struct Rect {
    Vector position;
    Vector size;

    void draw(uint32_t* frame_buffer, int width, int height, uint32_t color)
    {
        for (int y = position.y; y < size.y + position.y; y++)
        {
            if (y < 0 || y >= height)
                continue;

            for (int x = position.x; x < size.x + position.x; x++)
            {
                if (x < 0 || x >= width)
                    continue;

                uint32_t index = x + y * width;
                frame_buffer[index] = color;
            }
        }
    }
};

struct Circle {
    Vector position;
    int radius;

    void draw(uint32_t* frame_buffer, int width, int height, uint32_t color)
    {
        for (int y = -radius; y <= radius; y++)
        {
            int draw_y = position.y + y;
            if (draw_y < 0 || draw_y >= height)
                continue;

            for (int x = -radius; x <= radius; x++)
            {
                int draw_x = position.x + x;
                
                if (draw_x < 0 || draw_x >= width)
                    continue;   

                if (x*x + y*y > radius * radius)
                    continue;

                uint32_t index = draw_x + draw_y * width;
                frame_buffer[index] = color;
            }
        }
    }
};

struct SevenSeg {
    static constexpr uint32_t NUM_SEGS = 8;
    Rect segments[NUM_SEGS];
    bool segments_on[NUM_SEGS];

    SevenSeg() {}

    SevenSeg(int x, int y, int w, int h)
    {
        segments[0] = {(Vector) {x, y},             (Vector) {w, h}}; // a
        segments[1] = {(Vector) {x+w, y},           (Vector) {h, w}}; // b
        segments[2] = {(Vector) {x+w, y+w},         (Vector) {h, w}}; // c
        segments[3] = {(Vector) {x, y+w*2-h},       (Vector) {w, h}}; // d
        segments[4] = {(Vector) {x-h, y+w},         (Vector) {h, w}}; // e
        segments[5] = {(Vector) {x-h, y},           (Vector) {h, w}}; // f
        segments[6] = {(Vector) {x, y+w-h/2},       (Vector) {w, h}}; // g
        segments[7] = {(Vector) {x+w+h+h/2, y+w*2-h}, (Vector) {h, h}}; // dp

        for (int i = 0; i < NUM_SEGS; i++)
            segments_on[i] = false;
    }

    void draw(uint32_t* frame_buffer, int width, int height, uint32_t on_color, uint32_t off_color)
    {
        for (int i = 0; i < NUM_SEGS; i++)
        {
            uint32_t color = segments_on[i] ? on_color : off_color;
            segments[i].draw(frame_buffer, width, height, color);
        }
    }

    void setSegments(uint32_t segment_values)
    {
        for (int i = 0; i < NUM_SEGS; i++)
        {
            segments_on[i] = (segment_values >> i) & 1;
        }
    }
};

struct EaterSegs {
    static constexpr uint32_t NUM_DIGITS = 4;
    SevenSeg digits[NUM_DIGITS];

    EaterSegs() {}

    EaterSegs(int x, int y, int w, int h)
    {
        for (int i = 0; i < NUM_DIGITS; i++)
        {
            digits[i] = SevenSeg(x + (w + h * 6) * i, y, w, h);
        }
    }

    void draw(uint32_t* frame_buffer, int width, int height, uint32_t on_color, uint32_t off_color)
    {
        for (int i = 0; i < NUM_DIGITS; i++)
            digits[i].draw(frame_buffer, width, height, on_color, off_color);
    }

    void setDigit(uint32_t digit, uint32_t value)
    {
        digits[digit & 3].setSegments(value);
    }
};

struct LedRegister {
    std::vector<Circle> circles;
    uint32_t state;
    uint32_t register_bits;

    LedRegister() {}
    LedRegister(int x, int y, int radius, int bits)
    {
        for (int i = 0; i < bits; i++)
        {
            Vector position = {x + (radius * 3) * i, y};
            Circle circle = {position, radius};
            circles.push_back(circle);
        }
        state = 0;
        register_bits = bits;
    }

    void draw(uint32_t* frame_buffer, int width, int height, uint32_t on_color, uint32_t off_color)
    {
        for (int i = 0; i < register_bits; i++)
        {
            uint32_t bit_mask = 1 << (register_bits - 1 - i);
            uint32_t color = bit_mask & state ? on_color : off_color;
            circles[i].draw(frame_buffer, width, height, color);
        }
    }

    void setRegister(uint32_t value)
    {
        state = value;
    }
};

template<uint32_t W, uint32_t H, uint32_t S>
class EaterDisplay {
    public:

        EaterDisplay(uint32_t frequency, uint8_t& segments, uint8_t& com, uint8_t& counter, uint8_t& flags, uint16_t& control, uint8_t& a, uint8_t& b);
        ~EaterDisplay();

        void Process();

    private:

    GLFWwindow* window;

    uint32_t gl_buffer[W * H];
    uint32_t frame_buffer[W * H];
    uint32_t intermediate_buffer[W * H];
    uint32_t frequency_;
    uint32_t frame_tick_;

    EaterSegs segs_;
    uint8_t &segments_, &com_;

    LedRegister counter_leds_, flags_leds_, control_leds_, a_leds_, b_leds_;
    uint8_t &counter_, &flags_, &a_, &b_;
    uint16_t &control_;
};

template<uint32_t W, uint32_t H, uint32_t S>
EaterDisplay<W, H, S>::EaterDisplay(uint32_t frequency, uint8_t& segments, uint8_t& com, uint8_t& counter, uint8_t& flags, uint16_t& control, uint8_t& a, uint8_t& b)
: segments_(segments), com_(com), counter_(counter), flags_(flags), control_(control), a_(a), b_(b)
{
    /////////////////////////////////////
    // OpenGL Initialization
    /////////////////////////////////////

    const GLchar* vertexSource = R"glsl(
        #version 150 core
        in vec2 position;
        in vec2 texcoord;
        out vec2 Texcoord;
        void main()
        {
            Texcoord = texcoord;
            gl_Position = vec4(position, 0.0, 1.0);
        }
    )glsl";
    const GLchar* fragmentSource = R"glsl(
        #version 150 core
        in vec2 Texcoord;
        out vec4 outColor;
        uniform sampler2D tex;
        void main()
        {
            outColor = texture(tex, Texcoord);
        }
    )glsl";

    glfwInit();

    #ifdef __APPLE__
    glfwWindowHint (GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint (GLFW_CONTEXT_VERSION_MINOR, 2);
    glfwWindowHint (GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
    glfwWindowHint (GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    window = glfwCreateWindow(W, H, "verileater", nullptr, nullptr); // Windowed
    #else
    glfwWindowHint(GLFW_RESIZABLE, GL_FALSE);
    window = glfwCreateWindow(W, H, "verileater", nullptr, nullptr);
    #endif

    glfwSetKeyCallback(window, nullptr);

    glfwSwapInterval(1);
    glfwMakeContextCurrent(window);
    glewExperimental = GL_TRUE;
    glewInit();

    // Create Vertex Array Object
    GLuint vao;
    glGenVertexArrays(1, &vao);
    glBindVertexArray(vao);

    // Create a Vertex Buffer Object and copy the vertex data to it
    GLuint vbo;
    glGenBuffers(1, &vbo);

    GLfloat vertices[] = {
    //  Position      Color             Texcoords
        -1.0f,  1.0f,  0.0f, 0.0f, // Top-left
        1.0f,  1.0f,  1.0f, 0.0f, // Top-right
        1.0f, -1.0f,  1.0f, 1.0f, // Bottom-right
        -1.0f, -1.0f,  0.0f, 1.0f  // Bottom-left
    };

    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);

    // Create an element array
    GLuint ebo;
    glGenBuffers(1, &ebo);

    GLuint elements[] = {
        0, 1, 2,
        2, 3, 0
    };

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(elements), elements, GL_STATIC_DRAW);

    // Create and compile the vertex shader
    GLuint vertexShader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertexShader, 1, &vertexSource, NULL);
    glCompileShader(vertexShader);

    // Create and compile the fragment shader
    GLuint fragmentShader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragmentShader, 1, &fragmentSource, NULL);
    glCompileShader(fragmentShader);

    // Link the vertex and fragment shader into a shader program
    GLuint shaderProgram = glCreateProgram();
    glAttachShader(shaderProgram, vertexShader);
    glAttachShader(shaderProgram, fragmentShader);
    glBindFragDataLocation(shaderProgram, 0, "outColor");
    glLinkProgram(shaderProgram);
    glUseProgram(shaderProgram);

    // Specify the layout of the vertex data
    GLint posAttrib = glGetAttribLocation(shaderProgram, "position");
    glEnableVertexAttribArray(posAttrib);
    glVertexAttribPointer(posAttrib, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), 0);

    // GLint colAttrib = glGetAttribLocation(shaderProgram, "color");
    // glEnableVertexAttribArray(colAttrib);
    // glVertexAttribPointer(colAttrib, 3, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), (void*)(2 * sizeof(GLfloat)));

    GLint texAttrib = glGetAttribLocation(shaderProgram, "texcoord");
    glEnableVertexAttribArray(texAttrib);
    glVertexAttribPointer(texAttrib, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), (void*)(2 * sizeof(GLfloat)));

    // Load texture
    GLuint tex;
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, W, H, 0, GL_RGBA, GL_UNSIGNED_BYTE, gl_buffer);

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);

    /////////////////////////////////////
    // Device Initialization
    /////////////////////////////////////

    frequency_ = frequency;
    frame_tick_ = 0;

    uint32_t seg_w = S * 5;
    uint32_t seg_h = S * 1;

    uint32_t seg_x = W / 2 - ((seg_w + seg_h * 6) * 4) / 2;
    uint32_t seg_y = H / 2 - (seg_w * 2) / 2;

    segs_ = EaterSegs(20, 20, seg_w, seg_h);

    int right_leds = W - (6 * 3 * 8) - 15;

    counter_leds_ = LedRegister(right_leds, 30, 6, 4);
    flags_leds_ = LedRegister(right_leds, 60, 6, 2);
    control_leds_ = LedRegister(10, H - 30, 6, 16);
    a_leds_ = LedRegister(right_leds, 90, 6, 8);
    b_leds_ = LedRegister(right_leds, 120, 6, 8);

    for (size_t i = 0; i < W * H; i++)
        gl_buffer[i] = 0xFF202020;
}

template<uint32_t W, uint32_t H, uint32_t S>
EaterDisplay<W, H, S>::~EaterDisplay()
{
    if (window)
        free(window);
}

template<uint32_t W, uint32_t H, uint32_t S>
void EaterDisplay<W, H, S>::Process()
{
    // Update frame
    if (frame_tick_++ >= frequency_ / 60)
    {
        frame_tick_ = 0;
        
        segs_.draw(gl_buffer, W, H, 0xFF0000FF, 0xFF000042);
        counter_leds_.setRegister(counter_);
        counter_leds_.draw(gl_buffer, W, H, 0xFF00FF00, 0xFF004200);
        flags_leds_.setRegister(flags_);
        flags_leds_.draw(gl_buffer, W, H, 0xFFFFFF00, 0xFF424200);
        control_leds_.setRegister(control_);
        control_leds_.draw(gl_buffer, W, H, 0xFFFF0000, 0xFF420000);

        a_leds_.setRegister(a_);
        a_leds_.draw(gl_buffer, W, H, 0xFF00FF00, 0xFF004200);
        b_leds_.setRegister(b_);
        b_leds_.draw(gl_buffer, W, H, 0xFF00FF00, 0xFF004200);

        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, W, H, GL_RGBA, GL_UNSIGNED_BYTE, gl_buffer);
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, 0);
        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    for (int i = 0; i < segs_.NUM_DIGITS; i++)
    {
        if ((com_ >> i) & 1)
        {
            segs_.setDigit(i, segments_);
        }
    }    
}


#endif // EATER_DISPLAY_H
