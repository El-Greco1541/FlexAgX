from flexagx.assurance import install_guards
from fastapi import FastAPI, HTTPException
from flexagx.contracts import RenderRequest, RenderResult
from flexagx.compute import png_decode, png_encode, render_pixels
app=FastAPI(title='FlexAgX CPU Renderer Microserver',version='0.3.0')

install_guards(app)

@app.get('/health')
def health(): return {'status':'ok','service':'renderer'}

@app.post('/v1/render',response_model=RenderResult)
def api_render(req:RenderRequest):
    try:
        image=png_decode(req.image_png_base64)
        out=render_pixels(image,req.settings,req.lut,req.gain_ev)
        return RenderResult(image_png_base64=png_encode(out),width=image.shape[1],height=image.shape[0])
    except (ValueError,OSError) as e: raise HTTPException(status_code=422,detail=str(e)) from e
